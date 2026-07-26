# backend/app/workers/review_tasks.py
"""Review Celery tasks — review queue."""
from __future__ import annotations

from uuid import UUID

from app.constants.enums import GitHubReviewRunStatus
from app.core.database import get_db_context
from app.core.logging import get_logger
from app.services.github_review import mark_review_run_failed, run_review_run
from app.workers.async_runner import run_worker_async
from app.workers.celery_app import celery_app

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
                    "status": run.status.value,
                },
            )
            if run.status == GitHubReviewRunStatus.completed:
                _enqueue_reconcile(review_run_id)

    try:
        run_worker_async(_run())
    except Exception as exc:
        logger.error(
            "github_review_run_task_failed",
            extra={
                "review_run_id": review_run_id,
                "error": str(exc),
                "retries": self.request.retries,
            },
        )
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (2**self.request.retries)) from exc

        error_message = str(exc)

        async def _fail() -> None:
            async with get_db_context() as session:
                await mark_review_run_failed(
                    session,
                    review_run_id=UUID(review_run_id),
                    error_message=error_message,
                )
                await session.commit()

        try:
            run_worker_async(_fail())
        except Exception as mark_exc:  # noqa: BLE001
            logger.error(
                "github_review_run_mark_failed_error",
                extra={"review_run_id": review_run_id, "error": str(mark_exc)},
            )
        raise
