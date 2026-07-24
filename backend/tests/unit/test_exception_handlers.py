# backend/tests/unit/test_exception_handlers.py
"""Exception handler logging — reserved LogRecord keys."""
from unittest.mock import MagicMock, patch

import pytest
from starlette.requests import Request

from app.core.exception_handlers import platform_exception_handler
from app.core.exceptions import ServiceUnavailableError, UnauthorizedError


@pytest.mark.asyncio
async def test_platform_exception_handler_logs_4xx_without_reserved_extra_keys():
    request = MagicMock(spec=Request)
    exc = UnauthorizedError("Invalid token")

    with patch("app.core.exception_handlers.logger") as mock_logger:
        response = await platform_exception_handler(request, exc)

    assert response.status_code == 401
    mock_logger.info.assert_called_once()
    extra = mock_logger.info.call_args.kwargs["extra"]
    assert "message" not in extra
    assert extra["error_message"] == "Invalid token"
    assert extra["code"] == "unauthorized"


@pytest.mark.asyncio
async def test_platform_exception_handler_logs_5xx_without_reserved_extra_keys():
    request = MagicMock(spec=Request)
    exc = ServiceUnavailableError(message="Authentication service unavailable")

    with (
        patch("app.core.exception_handlers.logger") as mock_logger,
        patch("app.core.exception_handlers.capture_exception") as mock_capture,
    ):
        response = await platform_exception_handler(request, exc)

    assert response.status_code == 503
    mock_logger.error.assert_called_once()
    extra = mock_logger.error.call_args.kwargs["extra"]
    assert "message" not in extra
    assert extra["error_message"] == "Authentication service unavailable"
    mock_capture.assert_called_once_with(exc)
