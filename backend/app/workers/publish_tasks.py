# backend/app/workers/publish_tasks.py
"""Publish Celery tasks — github_publish queue."""
from __future__ import annotations

import asyncio
from uuid import UUID

from kombu.exceptions import OperationalError

from app.core.database import get_db_context
from app.core.logging import get_logger
from app.services.github_publish import (
    PublishJobRetryableError,
    mark_publish_job_failed,
    resolve_publish_job_id_for_review_run,
    run_publish_job,
)
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


async def _execute_publish_review_run(publish_job_id: str) -> None:
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


async def _finalize_inline_publish_failure(publish_job_id: str, error_message: str) -> None:
    try:
        logger.error(
            "github_publish_inline_failed",
            extra={"publish_job_id": publish_job_id, "error": error_message},
        )
        async with get_db_context() as session:
            await mark_publish_job_failed(
                session,
                publish_job_id=UUID(publish_job_id),
                error_message=error_message,
            )
            await session.commit()
    except Exception:
        logger.exception(
            "github_publish_inline_finalize_failed",
            extra={"publish_job_id": publish_job_id},
        )


async def _run_publish_review_run_inline(publish_job_id: str) -> None:
    try:
        await _execute_publish_review_run(publish_job_id)
    except asyncio.CancelledError:
        await _finalize_inline_publish_failure(publish_job_id, "inline publish cancelled")
        raise
    except (PublishJobRetryableError, Exception) as exc:  # noqa: BLE001
        await _finalize_inline_publish_failure(publish_job_id, str(exc))


def _inline_publish_task_done(publish_job_id: str, task: asyncio.Task[None]) -> None:
    if task.cancelled():
        return
    exc = task.exception()
    if exc is None or isinstance(exc, asyncio.CancelledError):
        return
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        asyncio.run(
            _finalize_inline_publish_failure(publish_job_id, f"inline publish failed: {exc}")
        )
        return
    loop.create_task(  # noqa: RUF006 — fire-and-forget failure cleanup
        _finalize_inline_publish_failure(publish_job_id, f"inline publish failed: {exc}")
    )


def _schedule_inline_publish_review_run(loop: asyncio.AbstractEventLoop, publish_job_id: str) -> None:
    task = loop.create_task(_run_publish_review_run_inline(publish_job_id))
    task.add_done_callback(lambda completed: _inline_publish_task_done(publish_job_id, completed))


def dispatch_publish_review_run(publish_job_id: str) -> None:
    """Enqueue publish work; run inline if the broker rejects the task."""
    try:
        publish_review_run.delay(publish_job_id)
    except (OperationalError, ConnectionError, OSError) as exc:
        logger.warning(
            "github_publish_enqueue_failed_running_inline",
            extra={"publish_job_id": publish_job_id, "error": str(exc)},
        )
        try:
            loop = asyncio.get_running_loop()
        except RuntimeError:
            publish_review_run.run(publish_job_id)
        else:
            _schedule_inline_publish_review_run(loop, publish_job_id)


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
    try:
        asyncio.run(_execute_publish_review_run(publish_job_id))
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

    async def _resolve_publish_job() -> str | None:
        async with get_db_context() as session:
            job_id, created = await resolve_publish_job_id_for_review_run(
                session,
                review_run_id=UUID(review_run_id),
            )
            if job_id is None:
                return None
            if created:
                await session.commit()
            return str(job_id)

    try:
        publish_job_id = asyncio.run(_resolve_publish_job())
        if publish_job_id is None:
            return
        dispatch_publish_review_run(publish_job_id)
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
