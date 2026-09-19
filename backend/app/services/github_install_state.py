# backend/app/services/github_install_state.py
"""HMAC install `state` for GitHub App Setup URL (Q13–Q14, Q20)."""
from __future__ import annotations

import base64
import binascii
import hashlib
import hmac
import json
import secrets
import time
from dataclasses import dataclass
from uuid import UUID

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError, ValidationError

SETUP_STASH_COOKIE = "revy_github_setup"
_INSTALL_KEYS = frozenset({"exp", "nonce", "user_id", "workspace_id"})
_OAUTH_KEYS = frozenset({"exp", "kind", "nonce"})
_STASH_KEYS = frozenset(
    {"exp", "installation_id", "nonce", "setup_action", "user_id", "workspace_id"}
)


@dataclass(frozen=True)
class InstallState:
    workspace_id: UUID
    user_id: UUID
    nonce: str
    exp: int


@dataclass(frozen=True)
class OAuthState:
    nonce: str
    exp: int


@dataclass(frozen=True)
class SetupStash:
    workspace_id: UUID
    user_id: UUID
    installation_id: int
    setup_action: str
    nonce: str
    exp: int


def _client_secret_bytes() -> bytes:
    raw = (settings.github_client_secret or "").strip()
    if not raw:
        raise ServiceUnavailableError(
            message="GitHub client secret is not configured",
            error_code="github_client_secret_missing",
        )
    return raw.encode()


def _b64url_encode(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b"=").decode("ascii")


def _b64url_decode(value: str) -> bytes:
    padding = "=" * (-len(value) % 4)
    try:
        return base64.urlsafe_b64decode(value + padding)
    except (binascii.Error, ValueError) as exc:
        raise ValidationError(message="Invalid install state", field="state") from exc


def _encode(payload: dict[str, object]) -> str:
    body = json.dumps(payload, separators=(",", ":"), sort_keys=True).encode()
    digest = hmac.new(_client_secret_bytes(), body, hashlib.sha256).digest()
    return f"{_b64url_encode(body)}.{_b64url_encode(digest)}"


def _decode_payload(token: str, *, required_keys: frozenset[str]) -> dict[str, object]:
    if not token or "." not in token:
        raise ValidationError(message="Invalid install state", field="state")
    body_b64, sig_b64 = token.split(".", 1)
    body = _b64url_decode(body_b64)
    given = _b64url_decode(sig_b64)
    expected = hmac.new(_client_secret_bytes(), body, hashlib.sha256).digest()
    if not hmac.compare_digest(expected, given):
        raise ValidationError(message="Invalid install state", field="state")
    try:
        payload = json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise ValidationError(message="Invalid install state", field="state") from exc
    if not isinstance(payload, dict) or set(payload) != required_keys:
        raise ValidationError(message="Invalid install state", field="state")
    return payload


def mint_install_state(
    *,
    workspace_id: UUID,
    user_id: UUID,
    now: int | None = None,
) -> str:
    issued_at = int(time.time()) if now is None else now
    payload = {
        "workspace_id": str(workspace_id),
        "user_id": str(user_id),
        "nonce": secrets.token_urlsafe(16),
        "exp": issued_at + settings.github_install_state_ttl_seconds,
    }
    return _encode(payload)


def verify_install_state(token: str, *, now: int | None = None) -> InstallState:
    payload = _decode_payload(token, required_keys=_INSTALL_KEYS)
    current = int(time.time()) if now is None else now
    try:
        exp = int(payload["exp"])
        workspace_id = UUID(str(payload["workspace_id"]))
        user_id = UUID(str(payload["user_id"]))
        nonce = str(payload["nonce"])
    except (TypeError, ValueError) as exc:
        raise ValidationError(message="Invalid install state", field="state") from exc
    if not nonce or exp <= current:
        raise ValidationError(message="Install state has expired", field="state")
    return InstallState(
        workspace_id=workspace_id,
        user_id=user_id,
        nonce=nonce,
        exp=exp,
    )


def mint_oauth_state(*, nonce: str, now: int | None = None) -> str:
    issued_at = int(time.time()) if now is None else now
    return _encode(
        {
            "kind": "oauth",
            "nonce": nonce,
            "exp": issued_at + settings.github_install_state_ttl_seconds,
        }
    )


def verify_oauth_state(token: str, *, now: int | None = None) -> OAuthState:
    payload = _decode_payload(token, required_keys=_OAUTH_KEYS)
    current = int(time.time()) if now is None else now
    try:
        exp = int(payload["exp"])
        nonce = str(payload["nonce"])
        kind = str(payload["kind"])
    except (TypeError, ValueError) as exc:
        raise ValidationError(message="Invalid install state", field="state") from exc
    if kind != "oauth" or not nonce or exp <= current:
        raise ValidationError(message="Install state has expired", field="state")
    return OAuthState(nonce=nonce, exp=exp)


def mint_setup_stash(
    *,
    workspace_id: UUID,
    user_id: UUID,
    installation_id: int,
    setup_action: str,
    nonce: str,
    now: int | None = None,
) -> str:
    issued_at = int(time.time()) if now is None else now
    return _encode(
        {
            "workspace_id": str(workspace_id),
            "user_id": str(user_id),
            "installation_id": installation_id,
            "setup_action": setup_action,
            "nonce": nonce,
            "exp": issued_at + settings.github_install_state_ttl_seconds,
        }
    )


def verify_setup_stash(token: str, *, now: int | None = None) -> SetupStash:
    payload = _decode_payload(token, required_keys=_STASH_KEYS)
    current = int(time.time()) if now is None else now
    try:
        exp = int(payload["exp"])
        workspace_id = UUID(str(payload["workspace_id"]))
        user_id = UUID(str(payload["user_id"]))
        installation_id = int(payload["installation_id"])
        setup_action = str(payload["setup_action"])
        nonce = str(payload["nonce"])
    except (TypeError, ValueError) as exc:
        raise ValidationError(message="Invalid install state", field="state") from exc
    if not nonce or installation_id <= 0 or exp <= current:
        raise ValidationError(message="Install state has expired", field="state")
    return SetupStash(
        workspace_id=workspace_id,
        user_id=user_id,
        installation_id=installation_id,
        setup_action=setup_action,
        nonce=nonce,
        exp=exp,
    )
