# backend/app/workers/index_tasks.py
"""Indexing Celery tasks — indexing queue."""
from __future__ import annotations

from uuid import UUID

from app.constants.enums import GitHubIndexJobStatus, ReviewProfile
from app.core.database import get_db_context
from app.core.logging import get_logger
from app.services.github_indexing import mark_index_job_failed, run_index_job
from app.services.github_review import enqueue_review_run
from app.services.review_pipeline import prepare_review_after_index
from app.workers.celery_app import celery_app
from app.workers.task_retries import run_with_retryable_failure

logger = get_logger(__name__)


@celery_app.task(
    name="app.workers.index_tasks.index_pull_request_revision",
    bind=True,
    max_retries=0,
    queue="indexing",
)
def index_pull_request_revision(self, index_job_id: str) -> None:
    review_run_ids: list[UUID] = []

    async def _run() -> None:
        nonlocal review_run_ids
        async with get_db_context() as session:
            job = await run_index_job(session, index_job_id=UUID(index_job_id))
            log_extra = {
                "index_job_id": index_job_id,
                "status": str(job.status),
                "chunk_count": job.chunk_count,
            }
            if job.status == GitHubIndexJobStatus.failed:
                log_extra["error_message"] = job.error_message
                logger.error("github_index_job_finished", extra=log_extra)
            else:
                logger.info("github_index_job_complete", extra=log_extra)
            review_run_id = await prepare_review_after_index(session, job)
            if review_run_id is not None:
                review_run_ids.append(review_run_id)

    async def _mark_failed(error_message: str) -> None:
        async with get_db_context() as session:
            await mark_index_job_failed(
                session,
                index_job_id=UUID(index_job_id),
                error_message=error_message,
            )
            await session.commit()

    run_with_retryable_failure(
        self,
        max_retries=self.max_retries,
        run=_run,
        mark_permanent_failure=_mark_failed,
        log_context={"index_job_id": index_job_id},
        logger=logger,
    )

    for review_run_id in review_run_ids:
        enqueue_review_run(review_run_id, profile=ReviewProfile.standard)
