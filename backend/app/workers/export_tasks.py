# backend/app/workers/export_tasks.py
"""Data export Celery tasks — ACCOUNT_LIFECYCLE.md."""
from __future__ import annotations

import asyncio
from uuid import UUID

from app.core.database import get_db_context
from app.core.logging import get_logger
from app.models.data_export_job import DataExportJobORM
from app.services.data_export import (
    build_export_payload,
    mark_completed,
    mark_failed,
    mark_processing,
    write_export_zip,
)
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(name="app.workers.export_tasks.run_data_export_job", bind=True, max_retries=2)
def run_data_export_job(self, job_id: str) -> None:
    parsed_id = UUID(job_id)

    async def _run() -> None:
        async with get_db_context() as session:
            job = await session.get(DataExportJobORM, parsed_id)
            if job is None:
                raise RuntimeError("export_job_not_found")
            await mark_processing(session, job_id=parsed_id)
            payload = await build_export_payload(session, user_id=job.user_id)
            storage_key, file_size = write_export_zip(job_id=parsed_id, payload=payload)
            await mark_completed(
                session,
                job_id=parsed_id,
                storage_key=storage_key,
                file_size_bytes=file_size,
            )

    try:
        asyncio.run(_run())
    except Exception as exc:
        error_message = str(exc)
        logger.error(
            "data_export_task_failed",
            extra={"job_id": job_id, "error": error_message, "retries": self.request.retries},
        )

        async def _fail() -> None:
            async with get_db_context() as session:
                await mark_failed(session, job_id=parsed_id, error_message=error_message)

        try:
            asyncio.run(_fail())
        except Exception as mark_exc:  # noqa: BLE001
            logger.error(
                "data_export_mark_failed_error",
                extra={"job_id": job_id, "error": str(mark_exc)},
            )

        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=30 * (2**self.request.retries)) from exc
