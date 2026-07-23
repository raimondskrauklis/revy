# backend/tests/unit/test_logging_config.py
"""LOG_LEVEL / LOG_FORMAT wiring."""
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
