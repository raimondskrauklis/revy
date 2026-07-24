# backend/tests/unit/test_exception_handlers.py
"""Exception handler logging — reserved LogRecord keys."""
from unittest.mock import MagicMock, patch

import pytest
from starlette.requests import Request

from app.core.exception_handlers import platform_exception_handler
from app.core.exceptions import UnauthorizedError


@pytest.mark.asyncio
async def test_platform_exception_handler_logs_without_reserved_extra_keys():
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
