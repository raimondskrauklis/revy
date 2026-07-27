# backend/app/workers/task_retries.py
"""Shared Celery retry helpers for pipeline workers."""
from __future__ import annotations

from collections.abc import Awaitable, Callable
from typing import TypeVar

from celery import Task

from app.core.worker_retries import celery_retry_countdown, classify_transient_error
from app.workers.async_runner import run_worker_async

T = TypeVar("T")


def run_with_retryable_failure(
    task: Task,
    *,
    max_retries: int,
    run: Callable[[], Awaitable[T]],
    mark_permanent_failure: Callable[[str], Awaitable[None]],
    log_context: dict[str, object],
    logger: object,
    base_seconds: int = 60,
) -> T:
    """Run async pipeline body; retry only classified transient failures."""
    try:
        return run_worker_async(run())
    except Exception as exc:
        retryable = classify_transient_error(exc)
        if retryable is not None and task.request.retries < max_retries:
            logger.warning(
                "pipeline_task_transient_failure",
                extra={**log_context, "error": str(exc), "retries": task.request.retries},
            )
            raise task.retry(
                exc=retryable,
                countdown=celery_retry_countdown(task.request.retries, base_seconds=base_seconds),
            ) from exc
        logger.error(
            "pipeline_task_failed",
            extra={**log_context, "error": str(exc), "retries": task.request.retries},
        )
        run_worker_async(mark_permanent_failure(str(exc)))
        raise
