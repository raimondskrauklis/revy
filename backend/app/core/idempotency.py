# backend/app/core/idempotency.py
"""Idempotency-Key handling — docs/backend/IDEMPOTENCY.md."""
from __future__ import annotations

import hashlib
import json
from typing import Annotated, Any

from fastapi import Depends, Request
from redis.asyncio import Redis
from starlette.responses import JSONResponse, Response

from app.core.rate_limit import get_redis
from app.core.security import app_secret_fingerprint

IDEMPOTENCY_HEADER = "Idempotency-Key"
IDEMPOTENCY_TTL_SECONDS = 60 * 60 * 24
IDEMPOTENCY_REDIS_PREFIX = f"idempotency:{app_secret_fingerprint(purpose='idempotency')}"


def _request_fingerprint(request: Request, body: bytes) -> str:
    payload = {
        "method": request.method,
        "path": request.url.path,
        "body": body.decode("utf-8", errors="replace"),
    }
    raw = json.dumps(payload, sort_keys=True).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


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
    if cached is None:
        request.state.idempotency_redis_key = redis_key
        request.state.idempotency_fingerprint = fingerprint
        return None

    data = json.loads(cached)
    if data.get("fingerprint") != fingerprint:
        return JSONResponse(
            status_code=409,
            content={
                "error": "conflict",
                "message": "Idempotency-Key reused with different request body",
            },
        )

    return JSONResponse(status_code=data["status_code"], content=data["body"])


async def store_idempotent_response(
    request: Request,
    response: Response,
    redis: Redis,
    *,
    user_sub: str,
) -> None:
    redis_key = getattr(request.state, "idempotency_redis_key", None)
    fingerprint = getattr(request.state, "idempotency_fingerprint", None)
    if redis_key is None or fingerprint is None:
        return
    if response.status_code < 200 or response.status_code >= 300:
        return

    body: Any
    if hasattr(response, "body") and response.body:
        body = json.loads(response.body)
    else:
        body = {}

    payload = {
        "fingerprint": fingerprint,
        "status_code": response.status_code,
        "body": body,
    }
    await redis.set(redis_key, json.dumps(payload), ex=IDEMPOTENCY_TTL_SECONDS)
