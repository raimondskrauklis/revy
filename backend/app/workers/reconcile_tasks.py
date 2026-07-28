# backend/app/workers/reconcile_tasks.py
"""Reconciliation Celery tasks — reconciliation queue."""
from __future__ import annotations

import time
from uuid import UUID

from app.core.database import get_db_context
from app.core.logging import get_logger
from app.models.github_review_run import GitHubReviewRunORM
from app.services.github_finding_judge import (
    JudgeCandidateArtifact,
    record_review_run_judge_status,
)
from app.services.github_finding_reconcile import reconcile_review_run
from app.services.github_generation_lifecycle import is_review_run_superseded
from app.services.github_pipeline_trace import (
    finalize_pipeline_github_check_for_review_run,
    get_pipeline_run_for_review_run,
    record_judge_pipeline_step,
    record_reconcile_pipeline_step,
)
from app.services.github_publish import enqueue_publish_for_review_run
from app.workers.async_runner import run_worker_async
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(
    name="app.workers.reconcile_tasks.reconcile_review_run",
    bind=True,
    max_retries=3,
    queue="reconciliation",
)
def reconcile_review_run_task(self, review_run_id: str) -> None:
    async def _run() -> None:
        async with get_db_context() as session:
            started = time.monotonic()
            group_ids = await reconcile_review_run(session, review_run_id=UUID(review_run_id))
            reconcile_duration_ms = int((time.monotonic() - started) * 1000)
            judge_artifacts: list[JudgeCandidateArtifact] = []
            judged = await record_review_run_judge_status(
                session,
                review_run_id=UUID(review_run_id),
                artifacts_out=judge_artifacts,
            )
            judge_duration_ms = int((time.monotonic() - started) * 1000) - reconcile_duration_ms

            pipeline_run = await get_pipeline_run_for_review_run(
                session,
                review_run_id=UUID(review_run_id),
            )
            if pipeline_run is not None:
                await record_reconcile_pipeline_step(
                    session,
                    pipeline_run_id=pipeline_run.id,
                    group_count=len(group_ids),
                    duration_ms=reconcile_duration_ms,
                )
                await record_judge_pipeline_step(
                    session,
                    pipeline_run_id=pipeline_run.id,
                    judged_count=judged,
                    duration_ms=max(judge_duration_ms, 0),
                    candidates=judge_artifacts,
                )

            review_run = await session.get(GitHubReviewRunORM, UUID(review_run_id))
            if review_run is not None and is_review_run_superseded(review_run):
                logger.info(
                    "publish_enqueue_skipped_superseded",
                    extra={"review_run_id": review_run_id},
                )
                await session.commit()
                return

            await session.commit()
            enqueue_publish_for_review_run(UUID(review_run_id))
            logger.info(
                "github_reconcile_complete",
                extra={
                    "review_run_id": review_run_id,
                    "group_count": len(group_ids),
                    "judge_outcomes": judged,
                },
            )

    try:
        run_worker_async(_run())
    except Exception as exc:
        logger.error(
            "github_reconcile_task_failed",
            extra={
                "review_run_id": review_run_id,
                "error": str(exc),
                "retries": self.request.retries,
            },
        )
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (2**self.request.retries)) from exc

        error_message = str(exc)

        async def _finalize() -> None:
            async with get_db_context() as session:
                await finalize_pipeline_github_check_for_review_run(
                    session,
                    review_run_id=UUID(review_run_id),
                    summary=error_message,
                )
                await session.commit()

        run_worker_async(_finalize())
        raise
