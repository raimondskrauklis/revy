# backend/app/services/observability_failure.py
"""Failure taxonomy helpers — pipeline observability."""
from __future__ import annotations

import httpx

from app.constants.enums import GitHubReviewRunFailureClass


def map_judge_log_failure_class(value: str) -> GitHubReviewRunFailureClass:
    if value == "parse" or value == "empty_body":
        return GitHubReviewRunFailureClass.parse_error
    if value == "http":
        return GitHubReviewRunFailureClass.provider_error
    return GitHubReviewRunFailureClass.provider_error


def classify_failure_class(exc: BaseException) -> GitHubReviewRunFailureClass:
    if isinstance(exc, httpx.TimeoutException):
        return GitHubReviewRunFailureClass.timeout
    if isinstance(exc, httpx.HTTPStatusError):
        status = exc.response.status_code
        if status == 429:
            return GitHubReviewRunFailureClass.rate_limit
        if status == 413:
            return GitHubReviewRunFailureClass.context_length
        return GitHubReviewRunFailureClass.provider_error
    if isinstance(exc, httpx.HTTPError):
        return GitHubReviewRunFailureClass.provider_error
    return GitHubReviewRunFailureClass.provider_error
