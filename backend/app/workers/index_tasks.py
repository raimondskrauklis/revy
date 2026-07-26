# backend/app/workers/index_tasks.py
"""Indexing Celery tasks — indexing queue."""
from __future__ import annotations

import asyncio
from uuid import UUID

from app.core.database import get_db_context
from app.core.logging import get_logger
from app.services.github_indexing import run_index_job
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(
    name="app.workers.index_tasks.index_pull_request_revision",
    bind=True,
    max_retries=3,
)
def index_pull_request_revision(self, index_job_id: str) -> None:
    async def _run() -> None:
        async with get_db_context() as session:
            job = await run_index_job(session, index_job_id=UUID(index_job_id))
            logger.info(
                "github_index_job_complete",
                extra={
                    "index_job_id": index_job_id,
                    "status": job.status.value,
                    "chunk_count": job.chunk_count,
                },
            )

    try:
        asyncio.run(_run())
    except Exception as exc:
        logger.error(
            "github_index_job_task_failed",
            extra={
                "index_job_id": index_job_id,
                "error": str(exc),
                "retries": self.request.retries,
            },
        )
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (2**self.request.retries)) from exc
        raise
