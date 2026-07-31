# backend/app/core/worker_retries.py
"""Celery worker retry policy — transient vs permanent pipeline failures."""

from __future__ import annotations

import httpx

# Align with Voyage/GitHub/LLM provider guidance: rate limits and server errors only.
RETRYABLE_HTTP_STATUS_CODES = frozenset({408, 429, 500, 502, 503, 504})


class WorkerRetryableError(Exception):
    """Transient failure — worker may retry with backoff after DB rollback."""


def is_retryable_http_status(status_code: int) -> bool:
    return status_code in RETRYABLE_HTTP_STATUS_CODES


def is_retryable_immediate_mutation_error(exc: BaseException) -> bool:
    """Whether a single immediate retry may help (excludes rate limits and client errors)."""
    from app.core.exceptions import RateLimitedError, ServiceUnavailableError

    if isinstance(exc, RateLimitedError):
        return False
    if isinstance(exc, ServiceUnavailableError):
        return True
    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code
        return is_retryable_http_status(status_code) and status_code != 429
    return classify_transient_error(exc) is not None


def classify_transient_error(exc: BaseException) -> WorkerRetryableError | None:
    """Map an exception to a retryable wrapper, or None when failure is permanent."""
    if isinstance(exc, WorkerRetryableError):
        return exc
    if isinstance(exc, httpx.TimeoutException):
        return WorkerRetryableError(str(exc))
    if isinstance(exc, httpx.HTTPStatusError):
        if is_retryable_http_status(exc.response.status_code):
            return WorkerRetryableError(str(exc))
        return None
    if isinstance(exc, httpx.TransportError):
        return WorkerRetryableError(str(exc))
    return None


def celery_retry_countdown(retries: int, *, base_seconds: int = 60) -> int:
    return base_seconds * (2**retries)
