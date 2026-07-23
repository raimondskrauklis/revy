# backend/tests/unit/test_auth_audience.py
"""JWT audience / azp allowlist — AUTH.md."""
from unittest.mock import patch

import pytest

from app.core.auth import _validate_audience, token_client_allowlist
from app.core.exceptions import UnauthorizedError


def test_token_client_allowlist_includes_api_and_frontend():
    with (
        patch("app.core.auth.settings.keycloak_client_id", "revy-api"),
        patch("app.core.auth.settings.keycloak_frontend_client_id", "revy-web"),
    ):
        assert token_client_allowlist() == frozenset({"revy-api", "revy-web"})


def test_validate_audience_accepts_known_azp():
    with (
        patch("app.core.auth.settings.keycloak_client_id", "revy-api"),
        patch("app.core.auth.settings.keycloak_frontend_client_id", "revy-web"),
    ):
        _validate_audience({"azp": "revy-web", "aud": "revy-api"})


def test_validate_audience_rejects_unknown_azp():
    with (
        patch("app.core.auth.settings.keycloak_client_id", "revy-api"),
        patch("app.core.auth.settings.keycloak_frontend_client_id", "revy-web"),
    ):
        with pytest.raises(UnauthorizedError, match="authorized party"):
            _validate_audience({"azp": "evil-client", "aud": "revy-api"})
