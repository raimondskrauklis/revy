# backend/app/workers/index_tasks.py
"""Indexing Celery tasks — indexing queue."""
from __future__ import annotations

import time
from uuid import UUID

from app.constants.enums import GitHubIndexJobStatus, GitHubIndexJobTriggerSource, ReviewProfile
from app.core.database import get_db_context
from app.core.logging import get_logger
from app.models.github_index_job import GitHubIndexJobORM
from app.models.github_pull_request import GitHubPullRequestRevisionORM
from app.services.github_indexing import mark_index_job_failed, run_index_job
from app.services.github_pipeline_trace import (
    ensure_pipeline_run_for_index_job,
    finalize_pipeline_github_check_failure,
    finalize_pipeline_github_check_for_index_job,
    record_index_pipeline_step,
    start_pipeline_github_check,
    stash_pipeline_github_check_run_id,
)
from app.services.github_review import enqueue_review_run
from app.services.review_pipeline import prepare_review_after_index
from app.workers.celery_app import celery_app
from app.workers.task_retries import run_with_retryable_failure

logger = get_logger(__name__)

_PIPELINE_TRIGGERS = frozenset({
    GitHubIndexJobTriggerSource.autostart,
    GitHubIndexJobTriggerSource.command,
})


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
            pending_job = await session.get(GitHubIndexJobORM, UUID(index_job_id))
            if pending_job is None:
                return

            pipeline_run = None
            github_check_run_id = None
            if pending_job.trigger_source in _PIPELINE_TRIGGERS:
                revision = await session.get(GitHubPullRequestRevisionORM, pending_job.revision_id)
                if revision is not None:
                    pipeline_run = await ensure_pipeline_run_for_index_job(
                        session,
                        job=pending_job,
                        head_sha=revision.head_sha,
                    )
                    github_check_run_id = await start_pipeline_github_check(
                        session,
                        pipeline_run=pipeline_run,
                    )
                    if github_check_run_id is not None:
                        await stash_pipeline_github_check_run_id(
                            session,
                            pipeline_run_id=pipeline_run.id,
                            github_check_run_id=github_check_run_id,
                        )
                    await session.flush()

            started = time.monotonic()
            job = await run_index_job(session, index_job_id=UUID(index_job_id))
            duration_ms = int((time.monotonic() - started) * 1000)

            if pipeline_run is not None:
                await record_index_pipeline_step(
                    session,
                    pipeline_run_id=pipeline_run.id,
                    job=job,
                    duration_ms=duration_ms,
                    github_check_run_id=github_check_run_id,
                )
                if job.status == GitHubIndexJobStatus.failed:
                    await finalize_pipeline_github_check_failure(
                        session,
                        pipeline_run_id=pipeline_run.id,
                        summary=job.error_message or "Index job failed",
                    )

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
            review_outcome = await prepare_review_after_index(session, job)
            if review_outcome.review_run_id is not None:
                review_run_ids.append(review_outcome.review_run_id)
            elif (
                pipeline_run is not None
                and job.status == GitHubIndexJobStatus.completed
                and review_outcome.fail_pipeline_check
            ):
                await finalize_pipeline_github_check_failure(
                    session,
                    pipeline_run_id=pipeline_run.id,
                    summary=review_outcome.pipeline_check_summary or "Review was not enqueued",
                )

    async def _mark_failed(error_message: str) -> None:
        async with get_db_context() as session:
            await mark_index_job_failed(
                session,
                index_job_id=UUID(index_job_id),
                error_message=error_message,
            )
            await finalize_pipeline_github_check_for_index_job(
                session,
                index_job_id=UUID(index_job_id),
                summary=error_message,
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
