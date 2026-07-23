# backend/tests/unit/test_logging_config.py
"""LOG_LEVEL / LOG_FORMAT wiring."""
import json
import logging
from unittest.mock import patch

import pytest

from app.core.logging import configure_logging


def test_configure_logging_console_format():
    with (
        patch("app.core.config.settings.log_level", "DEBUG"),
        patch("app.core.config.settings.log_format", "console"),
    ):
        configure_logging()
        root = logging.getLogger()
        assert root.level == logging.DEBUG
        assert isinstance(root.handlers[0].formatter.__class__.__name__, str)


def test_configure_logging_rejects_unknown_format():
    with patch("app.core.config.settings.log_format", "xml"):
        with pytest.raises(ValueError, match="LOG_FORMAT"):
            configure_logging()


def test_json_formatter_merges_log_record_extras():
    from app.core.logging import JsonFormatter

    formatter = JsonFormatter()
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg="request_completed",
        args=(),
        exc_info=None,
    )
    record.method = "GET"
    record.path = "/health"
    record.status_code = 200
    record.duration_ms = 12

    payload = json.loads(formatter.format(record))

    assert payload["message"] == "request_completed"
    assert payload["method"] == "GET"
    assert payload["path"] == "/health"
    assert payload["status_code"] == 200
    assert payload["duration_ms"] == 12
