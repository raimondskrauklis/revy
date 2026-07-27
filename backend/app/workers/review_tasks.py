# backend/app/workers/review_tasks.py
"""Review Celery tasks — review queue."""
from __future__ import annotations

from uuid import UUID

from app.constants.enums import GitHubReviewRunStatus
from app.core.database import get_db_context
from app.core.logging import get_logger
from app.services.github_review import mark_review_run_failed, run_review_run
from app.workers.celery_app import celery_app
from app.workers.task_retries import run_with_retryable_failure

logger = get_logger(__name__)


def _enqueue_reconcile(review_run_id: str) -> None:
    from app.workers.reconcile_tasks import reconcile_review_run_task

    reconcile_review_run_task.delay(review_run_id)


@celery_app.task(
    name="app.workers.review_tasks.review_pull_request_revision",
    bind=True,
    max_retries=3,
    queue="review",
)
def review_pull_request_revision(self, review_run_id: str) -> None:
    async def _run() -> None:
        async with get_db_context() as session:
            run = await run_review_run(session, review_run_id=UUID(review_run_id))
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
            await session.commit()

    run_with_retryable_failure(
        self,
        max_retries=self.max_retries,
        run=_run,
        mark_permanent_failure=_mark_failed,
        log_context={"review_run_id": review_run_id},
        logger=logger,
    )
