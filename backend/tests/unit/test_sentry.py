# backend/tests/unit/test_sentry.py
"""Sentry helper gates — no network calls when DSN unset."""

from unittest.mock import patch

import pytest

from app.core import sentry as sentry_module


@pytest.mark.parametrize(
    ("dsn", "environment", "enable_in_test", "expected"),
    [
        (None, "development", False, False),
        ("https://example@o0.ingest.sentry.io/1", "development", False, True),
        ("https://example@o0.ingest.sentry.io/1", "test", False, False),
        ("https://example@o0.ingest.sentry.io/1", "test", True, True),
    ],
)
def test_should_capture_sentry(dsn, environment, enable_in_test, expected):
    with patch.object(sentry_module.settings, "sentry_dsn", dsn):
        with patch.object(sentry_module.settings, "environment", environment):
            with patch.object(sentry_module.settings, "sentry_enable_in_test", enable_in_test):
                assert sentry_module.should_capture_sentry() is expected


def test_capture_exception_noop_without_dsn():
    with patch.object(sentry_module, "should_capture_sentry", return_value=False):
        with patch.object(sentry_module.sentry_sdk, "capture_exception") as capture:
            sentry_module.capture_exception(RuntimeError("boom"))
            capture.assert_not_called()


def test_capture_exception_forwards_when_enabled():
    exc = RuntimeError("boom")
    with patch.object(sentry_module, "should_capture_sentry", return_value=True):
        with patch.object(sentry_module.sentry_sdk, "capture_exception") as capture:
            sentry_module.capture_exception(exc)
            capture.assert_called_once_with(exc)


def test_init_sentry_skips_without_dsn():
    with patch.object(sentry_module, "should_capture_sentry", return_value=False):
        with patch.object(sentry_module.sentry_sdk, "init") as init:
            sentry_module.init_sentry()
            init.assert_not_called()


def test_init_sentry_calls_sdk_when_enabled():
    with patch.object(sentry_module, "should_capture_sentry", return_value=True):
        with patch.object(sentry_module.settings, "sentry_dsn", "https://example@o0.ingest.sentry.io/1"):
            with patch.object(sentry_module.settings, "environment", "development"):
                with patch.object(sentry_module.settings, "app_version", "1.0.0"):
                    with patch.object(sentry_module.settings, "sentry_send_default_pii", False):
                        with patch.object(sentry_module.settings, "sentry_traces_sample_rate_debug", 1.0):
                            with patch.object(sentry_module.settings, "sentry_traces_sample_rate_prod", 0.1):
                                with patch.object(sentry_module.sentry_sdk, "init") as init:
                                    sentry_module.init_sentry()
                                    init.assert_called_once()
                                    assert init.call_args.kwargs["dsn"] == "https://example@o0.ingest.sentry.io/1"
