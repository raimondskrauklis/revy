# backend/tests/unit/test_security.py
"""SECRET_KEY derived namespaces."""
from unittest.mock import patch

from app.core.security import app_secret_fingerprint


def test_app_secret_fingerprint_stable_for_purpose():
    with patch("app.core.config.settings.secret_key", "test-secret"):
        a = app_secret_fingerprint(purpose="idempotency")
        b = app_secret_fingerprint(purpose="idempotency")
        c = app_secret_fingerprint(purpose="other")
    assert a == b
    assert a != c
    assert len(a) == 16
