# backend/app/workers/publish_tasks.py
"""Publish Celery tasks — github_publish queue."""
from __future__ import annotations

import asyncio
from uuid import UUID

from sqlalchemy import select

from app.constants.enums import GitHubPublishJobStatus, GitHubReviewRunStatus
from app.core.database import get_db_context
from app.core.logging import get_logger
from app.models.github_publish_job import GitHubPublishJobORM
from app.models.github_pull_request import GitHubPullRequestRevisionORM
from app.models.github_review_run import GitHubReviewRunORM
from app.services.github_publish import run_publish_job
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(
    name="app.workers.publish_tasks.publish_review_run",
    bind=True,
    max_retries=3,
    queue="github_publish",
)
def publish_review_run(self, publish_job_id: str) -> None:
    async def _run() -> None:
        async with get_db_context() as session:
            job = await run_publish_job(session, publish_job_id=UUID(publish_job_id))
            await session.commit()
            logger.info(
                "github_publish_complete",
                extra={
                    "publish_job_id": publish_job_id,
                    "status": job.status.value,
                    "check_run_id": job.github_check_run_id,
                },
            )

    try:
        asyncio.run(_run())
    except Exception as exc:
        logger.error(
            "github_publish_task_failed",
            extra={
                "publish_job_id": publish_job_id,
                "error": str(exc),
                "retries": self.request.retries,
            },
        )
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (2**self.request.retries)) from exc
        raise


@celery_app.task(
    name="app.workers.publish_tasks.publish_for_review_run",
    bind=True,
    max_retries=3,
    queue="github_publish",
)
def publish_for_review_run(self, review_run_id: str) -> None:
    async def _run() -> None:
        async with get_db_context() as session:
            run = await session.get(GitHubReviewRunORM, UUID(review_run_id))
            if run is None or run.status != GitHubReviewRunStatus.completed:
                return

            pending = await session.scalar(
                select(GitHubPublishJobORM.id)
                .where(
                    GitHubPublishJobORM.review_run_id == run.id,
                    GitHubPublishJobORM.status.in_(
                        (GitHubPublishJobStatus.pending, GitHubPublishJobStatus.processing),
                    ),
                )
                .limit(1)
            )
            if pending is not None:
                return

            revision = await session.get(GitHubPullRequestRevisionORM, run.revision_id)
            if revision is None:
                return

            job = GitHubPublishJobORM(
                review_run_id=run.id,
                revision_id=run.revision_id,
                workspace_id=run.workspace_id,
                head_sha=revision.head_sha,
                status=GitHubPublishJobStatus.pending,
            )
            session.add(job)
            await session.flush()

            result = await run_publish_job(session, publish_job_id=job.id)
            await session.commit()
            logger.info(
                "github_publish_for_review_run_complete",
                extra={
                    "review_run_id": review_run_id,
                    "publish_job_id": str(job.id),
                    "status": result.status.value,
                },
            )

    try:
        asyncio.run(_run())
    except Exception as exc:
        logger.error(
            "github_publish_for_review_run_failed",
            extra={
                "review_run_id": review_run_id,
                "error": str(exc),
                "retries": self.request.retries,
            },
        )
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (2**self.request.retries)) from exc
        raise
