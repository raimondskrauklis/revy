# backend/app/core/jwks.py
"""Keycloak JWKS fetch + cache — see docs/backend/AUTH.md."""
from __future__ import annotations

import asyncio
from datetime import UTC, datetime, timedelta
from typing import Any

import httpx
import jwt
from jwt import PyJWK, PyJWKSet
from jwt.exceptions import PyJWKSetError

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError
from app.core.logging import get_logger

logger = get_logger(__name__)

_JWKS_CACHE_TTL = timedelta(hours=1)


class JwkSigningKeyNotFoundError(Exception):
    """No signing JWK in the set matches the token ``kid`` header."""


def signing_keys_from_jwks(jwks: dict[str, Any]) -> list[PyJWK]:
    """Return signing keys from a JWKS document (``use: sig`` or unset, with ``kid``)."""
    jwk_set = PyJWKSet.from_dict(jwks)
    signing_keys = [
        key
        for key in jwk_set.keys
        if key.public_key_use in ("sig", None) and key.key_id
    ]
    if not signing_keys:
        raise PyJWKSetError("The JWKS endpoint did not contain any signing keys")
    return signing_keys


def signing_key_from_jwt(jwks: dict[str, Any], token: str) -> PyJWK:
    """Resolve the RS256 signing key for a JWT using ``kid`` and cached JWKS."""
    kid = jwt.get_unverified_header(token).get("kid")
    if not kid:
        raise jwt.InvalidTokenError("Token header missing kid")

    signing_keys = signing_keys_from_jwks(jwks)
    for key in signing_keys:
        if key.key_id == kid:
            return key

    raise JwkSigningKeyNotFoundError(f'No signing key matches kid: "{kid}"')


class JwksClient:
    _client: httpx.AsyncClient | None = None

    def __init__(self) -> None:
        self._keys: dict[str, Any] | None = None
        self._fetched_at: datetime | None = None
        self._lock = asyncio.Lock()

    @property
    def certs_url(self) -> str:
        base = settings.keycloak_url.rstrip("/")
        return f"{base}/realms/{settings.keycloak_realm}/protocol/openid-connect/certs"

    @property
    def issuer(self) -> str:
        return settings.keycloak_token_issuer

    async def _http_client(self) -> httpx.AsyncClient:
        if self.__class__._client is None or self.__class__._client.is_closed:
            self.__class__._client = httpx.AsyncClient(timeout=10.0)
        return self.__class__._client

    async def close(self) -> None:
        if self.__class__._client and not self.__class__._client.is_closed:
            await self.__class__._client.aclose()
            self.__class__._client = None

    async def get_jwks(self, *, force_refresh: bool = False) -> dict[str, Any]:
        async with self._lock:
            now = datetime.now(UTC)
            if (
                not force_refresh
                and self._keys is not None
                and self._fetched_at is not None
                and now - self._fetched_at < _JWKS_CACHE_TTL
            ):
                return self._keys

            try:
                client = await self._http_client()
                response = await client.get(self.certs_url)
                response.raise_for_status()
                self._keys = response.json()
                self._fetched_at = now
                logger.info("jwks_fetched", extra={"operation": "jwks_fetch"})
                return self._keys
            except httpx.HTTPError as exc:
                logger.error("jwks_fetch_failed", extra={"operation": "jwks_fetch"})
                if self._keys is not None:
                    logger.warning("jwks_using_stale_cache", extra={"operation": "jwks_fetch"})
                    return self._keys
                raise ServiceUnavailableError(
                    message="Authentication service unavailable",
                    details={"reason": str(exc)},
                ) from exc

    async def invalidate(self) -> None:
        async with self._lock:
            self._keys = None
            self._fetched_at = None


jwks_client = JwksClient()
