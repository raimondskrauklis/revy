# backend/app/core/exceptions.py
"""Domain exceptions — flat JSON via exception_handlers."""
from typing import Any

from fastapi import status


class PlatformException(Exception):
    http_status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "internal_error"

    def __init__(
        self,
        message: str,
        error_code: str | None = None,
        details: dict[str, Any] | None = None,
        field: str | None = None,
    ):
        self.message = message
        self.error_code = error_code or self.error_code
        self.details = details or {}
        self.field = field
        super().__init__(message)


class ValidationError(PlatformException):
    http_status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    error_code = "validation_error"


class NotFoundError(PlatformException):
    http_status_code = status.HTTP_404_NOT_FOUND
    error_code = "not_found"


class ConflictError(PlatformException):
    http_status_code = status.HTTP_409_CONFLICT
    error_code = "conflict"


class UnauthorizedError(PlatformException):
    http_status_code = status.HTTP_401_UNAUTHORIZED
    error_code = "unauthorized"


class ForbiddenError(PlatformException):
    http_status_code = status.HTTP_403_FORBIDDEN
    error_code = "forbidden"


class ServiceUnavailableError(PlatformException):
    http_status_code = status.HTTP_503_SERVICE_UNAVAILABLE
    error_code = "service_unavailable"


class BillingWebhookError(PlatformException):
    """Stripe webhook could not be applied — return 5xx so Stripe retries."""

    http_status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
    error_code = "billing_webhook_error"


class RateLimitedError(PlatformException):
    http_status_code = status.HTTP_429_TOO_MANY_REQUESTS
    error_code = "rate_limited"
