# backend/app/workers/publish_tasks.py
"""Publish Celery tasks — github_publish queue."""
from __future__ import annotations

import asyncio
from uuid import UUID

from app.core.database import get_db_context
from app.core.logging import get_logger
from app.services.github_publish import (
    PublishJobRetryableError,
    create_publish_job_for_review_run,
    mark_publish_job_failed,
    run_publish_job,
)
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


def _finalize_publish_failure(
    *,
    publish_job_id: str | None,
    exc: Exception,
    retries: int,
    max_retries: int,
) -> None:
    if publish_job_id is None or retries < max_retries:
        return

    async def _mark_failed() -> None:
        async with get_db_context() as session:
            await mark_publish_job_failed(
                session,
                publish_job_id=UUID(publish_job_id),
                error_message=str(exc),
            )
            await session.commit()

    asyncio.run(_mark_failed())


@celery_app.task(
    name="app.workers.publish_tasks.publish_review_run",
    bind=True,
    max_retries=3,
    queue="github_publish",
)
def publish_review_run(self, publish_job_id: str) -> None:
    async def _run() -> None:
        async with get_db_context() as session:
            job = await run_publish_job(
                session,
                publish_job_id=UUID(publish_job_id),
                persist_github_surface=True,
            )
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
    except (PublishJobRetryableError, Exception) as exc:
        logger.error(
            "github_publish_task_failed",
            extra={
                "publish_job_id": publish_job_id,
                "error": str(exc),
                "retries": self.request.retries,
            },
        )
        _finalize_publish_failure(
            publish_job_id=publish_job_id,
            exc=exc,
            retries=self.request.retries,
            max_retries=self.max_retries,
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
    publish_job_id: str | None = None

    async def _create_job() -> str | None:
        async with get_db_context() as session:
            job_id = await create_publish_job_for_review_run(
                session,
                review_run_id=UUID(review_run_id),
            )
            if job_id is None:
                return None
            await session.commit()
            return str(job_id)

    try:
        publish_job_id = asyncio.run(_create_job())
        if publish_job_id is None:
            return
        publish_review_run.delay(publish_job_id)
    except Exception as exc:
        logger.error(
            "github_publish_for_review_run_failed",
            extra={
                "review_run_id": review_run_id,
                "publish_job_id": publish_job_id,
                "error": str(exc),
                "retries": self.request.retries,
            },
        )
        _finalize_publish_failure(
            publish_job_id=publish_job_id,
            exc=exc,
            retries=self.request.retries,
            max_retries=self.max_retries,
        )
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (2**self.request.retries)) from exc
        raise
