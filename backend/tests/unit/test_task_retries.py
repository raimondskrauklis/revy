# backend/tests/unit/test_task_retries.py
"""Pipeline Celery task retry helper."""
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest
from celery.exceptions import Retry

from app.core.worker_retries import WorkerRetryableError
from app.workers import task_retries


def test_run_with_retryable_failure_retries_transient_error():
    task = MagicMock()
    task.request.retries = 0
    task.max_retries = 3
    task.retry = MagicMock(side_effect=Retry())

    response = httpx.Response(503, request=httpx.Request("POST", "https://api.example.com"))
    http_error = httpx.HTTPStatusError("unavailable", request=response.request, response=response)

    async def _run() -> None:
        raise http_error

    with patch("app.workers.task_retries.run_worker_async", side_effect=http_error):
        with pytest.raises(Retry):
            task_retries.run_with_retryable_failure(
                task,
                max_retries=3,
                run=_run,
                mark_permanent_failure=AsyncMock(),
                log_context={"review_run_id": "id"},
                logger=MagicMock(),
            )

    task.retry.assert_called_once()


def test_run_with_retryable_failure_marks_permanent_error_without_retry():
    task = MagicMock()
    task.request.retries = 0
    mark_failed = AsyncMock()

    bug = AttributeError("'str' object has no attribute 'value'")

    async def _run() -> None:
        raise bug

    with patch("app.workers.task_retries.run_worker_async", side_effect=bug):
        with pytest.raises(AttributeError):
            task_retries.run_with_retryable_failure(
                task,
                max_retries=3,
                run=_run,
                mark_permanent_failure=mark_failed,
                log_context={"review_run_id": "id"},
                logger=MagicMock(),
            )

    task.retry.assert_not_called()
    mark_failed.assert_called_once()


def test_run_with_retryable_failure_marks_failed_when_retries_exhausted():
    task = MagicMock()
    task.request.retries = 3
    mark_failed = AsyncMock()
    retryable = WorkerRetryableError("still rate limited")

    async def _run() -> None:
        raise retryable

    with patch("app.workers.task_retries.run_worker_async", side_effect=retryable):
        with pytest.raises(WorkerRetryableError):
            task_retries.run_with_retryable_failure(
                task,
                max_retries=3,
                run=_run,
                mark_permanent_failure=mark_failed,
                log_context={"review_run_id": "id"},
                logger=MagicMock(),
            )

    task.retry.assert_not_called()
    mark_failed.assert_called_once()
