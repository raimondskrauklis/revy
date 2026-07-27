# backend/app/workers/pipeline_purge_tasks.py
"""Pipeline artifact retention purge — review-quality O8."""
from __future__ import annotations

from app.core.database import get_db_context
from app.core.logging import get_logger
from app.services.github_pipeline_trace import purge_old_pipeline_artifacts
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(
    name="app.workers.pipeline_purge_tasks.purge_old_pipeline_artifacts",
    bind=True,
    max_retries=1,
    queue="maintenance",
)
def purge_old_pipeline_artifacts_task(self) -> int:
    async def _run() -> int:
        async with get_db_context() as session:
            deleted = await purge_old_pipeline_artifacts(session)
            await session.commit()
            return deleted

    from app.workers.async_runner import run_worker_async

    try:
        deleted = run_worker_async(_run())
        logger.info("pipeline_purge_task_complete", extra={"deleted_runs": deleted})
        return deleted
    except Exception as exc:
        logger.error("pipeline_purge_task_failed", extra={"error": str(exc)})
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=300) from exc
        raise
