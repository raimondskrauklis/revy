# backend/tests/unit/test_worker_retries.py
"""Worker retry policy — transient vs permanent failures."""
import httpx

from app.core.worker_retries import (
    WorkerRetryableError,
    celery_retry_countdown,
    classify_transient_error,
    is_retryable_http_status,
)


def test_is_retryable_http_status():
    assert is_retryable_http_status(429)
    assert is_retryable_http_status(503)
    assert not is_retryable_http_status(400)
    assert not is_retryable_http_status(422)


def test_classify_transient_error_attribute_error_is_permanent():
    assert classify_transient_error(AttributeError("'str' object has no attribute 'value'")) is None


def test_classify_transient_error_timeout_is_retryable():
    result = classify_transient_error(httpx.ReadTimeout("timed out"))
    assert isinstance(result, WorkerRetryableError)


def test_classify_transient_error_http_429_is_retryable():
    response = httpx.Response(429, request=httpx.Request("POST", "https://api.example.com"))
    exc = httpx.HTTPStatusError("rate limited", request=response.request, response=response)
    result = classify_transient_error(exc)
    assert isinstance(result, WorkerRetryableError)


def test_classify_transient_error_http_400_is_permanent():
    response = httpx.Response(400, request=httpx.Request("POST", "https://api.example.com"))
    exc = httpx.HTTPStatusError("bad request", request=response.request, response=response)
    assert classify_transient_error(exc) is None


def test_celery_retry_countdown_exponential():
    assert celery_retry_countdown(0) == 60
    assert celery_retry_countdown(1) == 120
    assert celery_retry_countdown(2) == 240
