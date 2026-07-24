# backend/tests/unit/test_decode_access_token.py
"""JWT decode with cached JWKS — issuer, audience, and rotation retry."""
from __future__ import annotations

import json
import time
from contextlib import ExitStack
from unittest.mock import AsyncMock, patch

import jwt
import pytest
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa
from jwt.algorithms import RSAAlgorithm

from app.core.auth import decode_access_token
from app.core.exceptions import ServiceUnavailableError, UnauthorizedError


def _rsa_jwks(*, kid: str = "test-kid") -> tuple[dict, bytes]:
    private_key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption(),
    )
    jwk_dict = json.loads(RSAAlgorithm.to_jwk(private_key.public_key()))
    jwk_dict.update({"kid": kid, "use": "sig", "alg": "RS256"})
    return {"keys": [jwk_dict]}, private_pem


def _auth_patches(*, jwks: dict, get_jwks: AsyncMock | None = None) -> ExitStack:
    stack = ExitStack()
    stack.enter_context(
        patch(
            "app.core.auth.jwks_client.get_jwks",
            new=get_jwks or AsyncMock(return_value=jwks),
        )
    )
    stack.enter_context(patch("app.core.auth.settings.keycloak_url", "https://auth.example"))
    stack.enter_context(patch("app.core.auth.settings.keycloak_realm", "revy"))
    stack.enter_context(patch("app.core.auth.settings.keycloak_client_id", "revy-api"))
    stack.enter_context(patch("app.core.auth.settings.keycloak_frontend_client_id", "revy-web"))
    return stack


@pytest.mark.asyncio
async def test_decode_access_token_validates_signature_and_audience():
    jwks, private_pem = _rsa_jwks()
    token = jwt.encode(
        {
            "sub": "user-1",
            "azp": "revy-web",
            "aud": "revy-api",
            "iss": "https://auth.example/realms/revy",
        },
        private_pem,
        algorithm="RS256",
        headers={"kid": "test-kid"},
    )

    with _auth_patches(jwks=jwks):
        payload = await decode_access_token(token)

    assert payload["sub"] == "user-1"


@pytest.mark.asyncio
async def test_decode_access_token_refreshes_jwks_on_key_rotation():
    jwks_old, _ = _rsa_jwks(kid="old-kid")
    jwks_new, private_pem_new = _rsa_jwks(kid="new-kid")
    token = jwt.encode(
        {
            "sub": "user-1",
            "azp": "revy-web",
            "iss": "https://auth.example/realms/revy",
        },
        private_pem_new,
        algorithm="RS256",
        headers={"kid": "new-kid"},
    )
    get_jwks = AsyncMock(side_effect=[jwks_old, jwks_new])

    with _auth_patches(jwks=jwks_old, get_jwks=get_jwks):
        payload = await decode_access_token(token)

    assert payload["sub"] == "user-1"
    assert get_jwks.await_count == 2
    get_jwks.assert_any_await(force_refresh=True)


@pytest.mark.asyncio
async def test_decode_access_token_rejects_invalid_signature_without_refresh():
    jwks, _ = _rsa_jwks()
    _, other_private_pem = _rsa_jwks(kid="other-kid")
    token = jwt.encode(
        {
            "sub": "user-1",
            "azp": "revy-web",
            "iss": "https://auth.example/realms/revy",
        },
        other_private_pem,
        algorithm="RS256",
        headers={"kid": "test-kid"},
    )
    get_jwks = AsyncMock(return_value=jwks)

    with _auth_patches(jwks=jwks, get_jwks=get_jwks):
        with pytest.raises(UnauthorizedError, match="Invalid token"):
            await decode_access_token(token)

    get_jwks.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_decode_access_token_expired_token_without_refresh():
    jwks, private_pem = _rsa_jwks()
    token = jwt.encode(
        {
            "sub": "user-1",
            "azp": "revy-web",
            "iss": "https://auth.example/realms/revy",
            "exp": int(time.time()) - 60,
        },
        private_pem,
        algorithm="RS256",
        headers={"kid": "test-kid"},
    )
    get_jwks = AsyncMock(return_value=jwks)

    with _auth_patches(jwks=jwks, get_jwks=get_jwks):
        with pytest.raises(UnauthorizedError, match="Token expired"):
            await decode_access_token(token)

    get_jwks.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_decode_access_token_rejects_invalid_audience_without_refresh():
    jwks, private_pem = _rsa_jwks()
    token = jwt.encode(
        {
            "sub": "user-1",
            "azp": "evil-client",
            "iss": "https://auth.example/realms/revy",
        },
        private_pem,
        algorithm="RS256",
        headers={"kid": "test-kid"},
    )
    get_jwks = AsyncMock(return_value=jwks)

    with _auth_patches(jwks=jwks, get_jwks=get_jwks):
        with pytest.raises(UnauthorizedError, match="authorized party"):
            await decode_access_token(token)

    get_jwks.assert_awaited_once_with()


@pytest.mark.asyncio
async def test_decode_access_token_unusable_jwks_returns_service_unavailable():
    _, private_pem = _rsa_jwks()
    token = jwt.encode(
        {
            "sub": "user-1",
            "azp": "revy-web",
            "iss": "https://auth.example/realms/revy",
        },
        private_pem,
        algorithm="RS256",
        headers={"kid": "test-kid"},
    )
    get_jwks = AsyncMock(return_value={"keys": []})

    with _auth_patches(jwks={"keys": []}, get_jwks=get_jwks):
        with pytest.raises(ServiceUnavailableError, match="Authentication service unavailable"):
            await decode_access_token(token)

    get_jwks.assert_awaited_once_with()
