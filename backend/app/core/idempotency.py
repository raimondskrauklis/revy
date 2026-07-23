# backend/app/core/idempotency.py
"""Idempotency-Key handling — docs/backend/IDEMPOTENCY.md."""
from __future__ import annotations

import asyncio
import hashlib
import json
from typing import Annotated, Any

from fastapi import Depends, Request
from redis.asyncio import Redis
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response

from app.core.auth import CurrentUser, get_current_user
from app.core.rate_limit import get_redis
from app.core.security import app_secret_fingerprint

IDEMPOTENCY_HEADER = "Idempotency-Key"
IDEMPOTENCY_TTL_SECONDS = 60 * 60 * 24
IDEMPOTENCY_IN_FLIGHT_TTL_SECONDS = 120
IDEMPOTENCY_POLL_ATTEMPTS = 30
IDEMPOTENCY_POLL_INTERVAL_SECONDS = 0.05
IDEMPOTENCY_REDIS_PREFIX = f"idempotency:{app_secret_fingerprint(purpose='idempotency')}"
_IN_FLIGHT_STATUS = "in_flight"


def _request_fingerprint(request: Request, body: bytes) -> str:
    payload = {
        "method": request.method,
        "path": request.url.path,
        "body": body.decode("utf-8", errors="replace"),
    }
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


def _in_flight_payload(*, fingerprint: str) -> str:
    return json.dumps({"status": _IN_FLIGHT_STATUS, "fingerprint": fingerprint})


def _response_from_cached(data: dict[str, Any], *, fingerprint: str) -> JSONResponse:
    if data.get("status") == _IN_FLIGHT_STATUS:
        if data.get("fingerprint") != fingerprint:
            return JSONResponse(
                status_code=409,
                content={
                    "error": "conflict",
                    "message": "Idempotency-Key reused with different request body",
                },
            )
        return JSONResponse(
            status_code=409,
            content={
                "error": "conflict",
                "message": "Duplicate request is already in progress",
            },
        )
    if data.get("fingerprint") != fingerprint:
        return JSONResponse(
            status_code=409,
            content={
                "error": "conflict",
                "message": "Idempotency-Key reused with different request body",
            },
        )
    return JSONResponse(status_code=data["status_code"], content=data["body"])


async def _poll_cached_response(
    redis: Redis,
    *,
    redis_key: str,
    fingerprint: str,
) -> JSONResponse | None:
    for _ in range(IDEMPOTENCY_POLL_ATTEMPTS):
        await asyncio.sleep(IDEMPOTENCY_POLL_INTERVAL_SECONDS)
        cached = await redis.get(redis_key)
        if cached is None:
            return None
        data = json.loads(cached)
        if data.get("status") != _IN_FLIGHT_STATUS:
            return _response_from_cached(data, fingerprint=fingerprint)
    cached = await redis.get(redis_key)
    if cached is None:
        return None
    return _response_from_cached(json.loads(cached), fingerprint=fingerprint)


async def load_idempotent_response(
    request: Request,
    redis: Annotated[Redis, Depends(get_redis)],
    *,
    user_sub: str,
) -> JSONResponse | None:
    key_header = request.headers.get(IDEMPOTENCY_HEADER)
    if not key_header or request.method.upper() != "POST":
        return None

    body = await request.body()
    fingerprint = _request_fingerprint(request, body)
    redis_key = f"{IDEMPOTENCY_REDIS_PREFIX}:{user_sub}:{key_header}"

    cached = await redis.get(redis_key)
    if cached is not None:
        return _response_from_cached(json.loads(cached), fingerprint=fingerprint)

    reserved = await redis.set(
        redis_key,
        _in_flight_payload(fingerprint=fingerprint),
        nx=True,
        ex=IDEMPOTENCY_IN_FLIGHT_TTL_SECONDS,
    )
    if reserved:
        request.state.idempotency_redis_key = redis_key
        request.state.idempotency_fingerprint = fingerprint
        return None

    polled = await _poll_cached_response(redis, redis_key=redis_key, fingerprint=fingerprint)
    if polled is not None:
        return polled

    request.state.idempotency_redis_key = redis_key
    request.state.idempotency_fingerprint = fingerprint
    return None


async def _read_response_bytes(response: Response) -> bytes:
    """Buffer response body — BaseHTTPMiddleware may not expose `.body`."""
    body = getattr(response, "body", None)
    if body:
        return bytes(body)
    chunks: list[bytes] = []
    async for chunk in response.body_iterator:
        chunks.append(chunk)
    return b"".join(chunks)


def _parse_json_response_body(body_bytes: bytes) -> Any | None:
    if not body_bytes:
        return None
    try:
        return json.loads(body_bytes)
    except json.JSONDecodeError:
        return None


async def release_idempotency_reservation(
    request: Request,
    redis: Redis,
) -> None:
    redis_key = getattr(request.state, "idempotency_redis_key", None)
    fingerprint = getattr(request.state, "idempotency_fingerprint", None)
    if redis_key is None or fingerprint is None:
        return

    cached = await redis.get(redis_key)
    if cached is None:
        return
    data = json.loads(cached)
    if data.get("status") == _IN_FLIGHT_STATUS and data.get("fingerprint") == fingerprint:
        await redis.delete(redis_key)


async def store_idempotent_response(
    request: Request,
    response: Response,
    redis: Redis,
    *,
    user_sub: str,
    body_bytes: bytes | None = None,
) -> None:
    redis_key = getattr(request.state, "idempotency_redis_key", None)
    fingerprint = getattr(request.state, "idempotency_fingerprint", None)
    if redis_key is None or fingerprint is None:
        return
    if response.status_code < 200 or response.status_code >= 300:
        await release_idempotency_reservation(request, redis)
        return

    raw = body_bytes if body_bytes is not None else await _read_response_bytes(response)
    body = _parse_json_response_body(raw)
    if body is None:
        await release_idempotency_reservation(request, redis)
        return

    payload = {
        "fingerprint": fingerprint,
        "status_code": response.status_code,
        "body": body,
    }
    await redis.set(redis_key, json.dumps(payload), ex=IDEMPOTENCY_TTL_SECONDS)


async def idempotency_guard(
    request: Request,
    redis: Annotated[Redis, Depends(get_redis)],
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> JSONResponse | None:
    """Return cached POST response when Idempotency-Key matches, else prime request.state."""
    request.state.idempotency_user_sub = current_user.sub
    return await load_idempotent_response(request, redis, user_sub=current_user.sub)


class IdempotencyStoreMiddleware(BaseHTTPMiddleware):
    """Persist successful POST responses keyed by Idempotency-Key + user sub."""

    async def dispatch(self, request: Request, call_next) -> Response:
        response = await call_next(request)
        if getattr(request.state, "idempotency_redis_key", None) is None:
            return response
        user_sub = getattr(request.state, "idempotency_user_sub", None)
        if user_sub is None:
            return response

        body_bytes = await _read_response_bytes(response)
        redis = await get_redis()
        await store_idempotent_response(
            request,
            response,
            redis,
            user_sub=user_sub,
            body_bytes=body_bytes,
        )

        if getattr(response, "body", None):
            return response

        return Response(
            content=body_bytes,
            status_code=response.status_code,
            headers=dict(response.headers),
            media_type=response.media_type,
        )
