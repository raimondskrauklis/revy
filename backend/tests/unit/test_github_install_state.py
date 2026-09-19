# backend/tests/unit/test_github_install_state.py
"""HMAC install state mint/verify — github-onboarding P0."""
import base64
import json
from unittest.mock import patch
from uuid import uuid4

import pytest

from app.core.exceptions import ServiceUnavailableError, ValidationError
from app.services.github_install_state import mint_install_state, verify_install_state


def _settings(*, secret: str = "github-client-secret", ttl: int = 1800):
    return patch(
        "app.services.github_install_state.settings",
        github_client_secret=secret,
        github_install_state_ttl_seconds=ttl,
    )


def test_mint_install_state_round_trips_workspace_and_user():
    workspace_id = uuid4()
    user_id = uuid4()
    with _settings():
        token = mint_install_state(workspace_id=workspace_id, user_id=user_id, now=1_700_000_000)
        parsed = verify_install_state(token, now=1_700_000_000)

    assert parsed.workspace_id == workspace_id
    assert parsed.user_id == user_id
    assert parsed.nonce
    assert parsed.exp == 1_700_000_000 + 1800


def test_verify_install_state_rejects_expired_token():
    with _settings(ttl=1800):
        token = mint_install_state(workspace_id=uuid4(), user_id=uuid4(), now=1_000_000)
        with pytest.raises(ValidationError, match="expired"):
            verify_install_state(token, now=1_000_000 + 1801)


def test_verify_install_state_rejects_flipped_workspace_id():
    workspace_id = uuid4()
    with _settings():
        token = mint_install_state(workspace_id=workspace_id, user_id=uuid4(), now=1_700_000_000)
        body_b64, sig_b64 = token.split(".", 1)
        padding = "=" * (-len(body_b64) % 4)
        body = json.loads(base64.urlsafe_b64decode(body_b64 + padding))
        body["workspace_id"] = str(uuid4())
        tampered_body = json.dumps(body, separators=(",", ":"), sort_keys=True).encode()
        tampered = (
            base64.urlsafe_b64encode(tampered_body).rstrip(b"=").decode("ascii") + "." + sig_b64
        )
        with pytest.raises(ValidationError, match="Invalid install state"):
            verify_install_state(tampered, now=1_700_000_000)


def test_mint_install_state_requires_client_secret():
    with _settings(secret=""):
        with pytest.raises(ServiceUnavailableError) as exc:
            mint_install_state(workspace_id=uuid4(), user_id=uuid4())
    assert exc.value.error_code == "github_client_secret_missing"
