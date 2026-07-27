# backend/app/workers/review_tasks.py
"""Review Celery tasks — review queue."""
from __future__ import annotations

from uuid import UUID

from app.constants.enums import GitHubReviewRunStatus, PipelineStepType
from app.core.database import get_db_context
from app.core.logging import get_logger
from app.services.github_pipeline_trace import (
    finalize_pipeline_github_check_failure,
    get_pipeline_run_for_review_run,
    pipeline_has_step,
    record_retrieve_pipeline_step,
    record_review_pipeline_step,
)
from app.services.github_review import mark_review_run_failed, run_review_run
from app.workers.celery_app import celery_app
from app.workers.task_retries import run_with_retryable_failure

logger = get_logger(__name__)


def _enqueue_reconcile(review_run_id: str) -> None:
    from app.workers.reconcile_tasks import reconcile_review_run_task

    reconcile_review_run_task.delay(review_run_id)


async def _record_review_pipeline_trace(
    session,
    *,
    review_run_id: UUID,
    outcome,
) -> None:
    run = outcome.run
    pipeline_run = await get_pipeline_run_for_review_run(session, review_run_id=run.id)
    if pipeline_run is None:
        return

    if await pipeline_has_step(
        session,
        pipeline_run_id=pipeline_run.id,
        step_type=PipelineStepType.review,
    ):
        return

    if outcome.context_pack is not None:
        await record_retrieve_pipeline_step(
            session,
            pipeline_run_id=pipeline_run.id,
            manifest=outcome.context_pack.manifest,
            duration_ms=outcome.retrieve_duration_ms,
        )

    await record_review_pipeline_step(
        session,
        pipeline_run_id=pipeline_run.id,
        run=run,
        prompt=outcome.context_pack.prompt if outcome.context_pack is not None else "",
        raw_response=outcome.raw_response,
        parse_report=outcome.parse_report
        or {"parsed_count": 0, "dropped_count": 0, "drop_reasons": {}},
        duration_ms=outcome.review_duration_ms,
    )

    if run.status == GitHubReviewRunStatus.failed:
        await finalize_pipeline_github_check_failure(
            session,
            pipeline_run_id=pipeline_run.id,
            summary=run.error_message or "Review run failed",
        )


@celery_app.task(
    name="app.workers.review_tasks.review_pull_request_revision",
    bind=True,
    max_retries=3,
    queue="review",
)
def review_pull_request_revision(self, review_run_id: str) -> None:
    async def _run() -> None:
        async with get_db_context() as session:
            outcome = await run_review_run(session, review_run_id=UUID(review_run_id))
            run = outcome.run
            await _record_review_pipeline_trace(session, review_run_id=run.id, outcome=outcome)
            await session.commit()
            logger.info(
                "github_review_run_complete",
                extra={
                    "review_run_id": review_run_id,
                    "status": str(run.status),
                },
            )
            if run.status == GitHubReviewRunStatus.completed:
                _enqueue_reconcile(review_run_id)

    async def _mark_failed(error_message: str) -> None:
        async with get_db_context() as session:
            await mark_review_run_failed(
                session,
                review_run_id=UUID(review_run_id),
                error_message=error_message,
            )
            pipeline_run = await get_pipeline_run_for_review_run(
                session,
                review_run_id=UUID(review_run_id),
            )
            if pipeline_run is not None:
                await finalize_pipeline_github_check_failure(
                    session,
                    pipeline_run_id=pipeline_run.id,
                    summary=error_message,
                )
            await session.commit()

    run_with_retryable_failure(
        self,
        max_retries=self.max_retries,
        run=_run,
        mark_permanent_failure=_mark_failed,
        log_context={"review_run_id": review_run_id},
        logger=logger,
    )
