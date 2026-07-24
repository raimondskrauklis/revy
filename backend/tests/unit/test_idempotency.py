# backend/tests/unit/test_idempotency.py
"""Idempotency-Key Redis cache — IDEMPOTENCY.md."""
import json
from unittest.mock import AsyncMock, MagicMock

import pytest
from starlette.requests import Request

from app.core.idempotency import (
    IDEMPOTENCY_REDIS_PREFIX,
    _request_fingerprint,
    load_idempotent_response,
    release_idempotency_reservation,
    store_idempotent_response,
)


def _make_request(
    *,
    method: str = "POST",
    path: str = "/api/v1/items",
    body: bytes = b'{"name":"Example"}',
    idempotency_key: str | None = "key-1",
) -> Request:
    headers = []
    if idempotency_key is not None:
        headers.append((b"idempotency-key", idempotency_key.encode()))
    scope = {
        "type": "http",
        "http_version": "1.1",
        "method": method,
        "path": path,
        "headers": headers,
        "query_string": b"",
    }
    request = Request(scope)

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    request._receive = receive
    return request


@pytest.mark.asyncio
async def test_load_idempotent_response_miss_primes_state():
    request = _make_request()
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)

    result = await load_idempotent_response(request, redis, user_sub="user-sub")

    assert result is None
    assert request.state.idempotency_redis_key == f"{IDEMPOTENCY_REDIS_PREFIX}:user-sub:key-1"
    assert request.state.idempotency_fingerprint == _request_fingerprint(request, b'{"name":"Example"}')
    redis.set.assert_awaited_once()


@pytest.mark.asyncio
async def test_load_idempotent_response_hit_returns_cached():
    request = _make_request()
    cached = {
        "fingerprint": _request_fingerprint(request, b'{"name":"Example"}'),
        "status_code": 201,
        "body": {"success": True, "data": {"id": "1"}},
    }
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=json.dumps(cached))

    result = await load_idempotent_response(request, redis, user_sub="user-sub")

    assert result is not None
    assert result.status_code == 201
    assert json.loads(result.body) == cached["body"]


@pytest.mark.asyncio
async def test_load_idempotent_response_mismatched_body_returns_409():
    request = _make_request()
    cached = {
        "fingerprint": "different",
        "status_code": 201,
        "body": {"success": True},
    }
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=json.dumps(cached))

    result = await load_idempotent_response(request, redis, user_sub="user-sub")

    assert result is not None
    assert result.status_code == 409


@pytest.mark.asyncio
async def test_load_idempotent_response_skips_without_header():
    request = _make_request(idempotency_key=None)
    redis = AsyncMock()

    result = await load_idempotent_response(request, redis, user_sub="user-sub")

    assert result is None
    redis.get.assert_not_called()


@pytest.mark.asyncio
async def test_store_idempotent_response_skips_empty_success_body():
    request = _make_request()
    fingerprint = _request_fingerprint(request, b'{"name":"Example"}')
    request.state.idempotency_redis_key = f"{IDEMPOTENCY_REDIS_PREFIX}:user-sub:key-1"
    request.state.idempotency_fingerprint = fingerprint

    response = MagicMock()
    response.status_code = 201
    response.body = b""

    redis = AsyncMock()
    redis.get = AsyncMock(
        return_value=json.dumps({"status": "in_flight", "fingerprint": fingerprint})
    )
    redis.delete = AsyncMock()
    redis.set = AsyncMock()

    await store_idempotent_response(request, response, redis, user_sub="user-sub", body_bytes=b"")

    redis.set.assert_not_called()
    redis.delete.assert_awaited_once()


@pytest.mark.asyncio
async def test_store_idempotent_response_persists_success():
    request = _make_request()
    request.state.idempotency_redis_key = f"{IDEMPOTENCY_REDIS_PREFIX}:user-sub:key-1"
    request.state.idempotency_fingerprint = _request_fingerprint(request, b'{"name":"Example"}')

    response = MagicMock()
    response.status_code = 201
    response.body = json.dumps({"success": True, "data": {"id": "1"}}).encode()

    redis = AsyncMock()
    redis.set = AsyncMock()

    await store_idempotent_response(request, response, redis, user_sub="user-sub")

    redis.set.assert_awaited_once()
    args = redis.set.await_args
    assert args[0][0] == f"{IDEMPOTENCY_REDIS_PREFIX}:user-sub:key-1"
    stored = json.loads(args[0][1])
    assert stored["status_code"] == 201
    assert stored["body"]["success"] is True


@pytest.mark.asyncio
async def test_store_idempotent_response_skips_non_success():
    request = _make_request()
    request.state.idempotency_redis_key = "key"
    request.state.idempotency_fingerprint = "fp"

    response = MagicMock()
    response.status_code = 422
    response.body = b""

    redis = AsyncMock()
    redis.get = AsyncMock(return_value='{"status":"in_flight","fingerprint":"fp"}')
    redis.delete = AsyncMock()
    await store_idempotent_response(request, response, redis, user_sub="user-sub")

    redis.set.assert_not_called()
    redis.delete.assert_awaited_once_with("key")


@pytest.mark.asyncio
async def test_release_idempotency_reservation_clears_in_flight():
    request = _make_request()
    request.state.idempotency_redis_key = "key"
    request.state.idempotency_fingerprint = "fp"

    redis = AsyncMock()
    redis.get = AsyncMock(return_value='{"status":"in_flight","fingerprint":"fp"}')
    redis.delete = AsyncMock()

    await release_idempotency_reservation(request, redis)

    redis.delete.assert_awaited_once_with("key")


@pytest.mark.asyncio
async def test_load_idempotent_response_in_flight_returns_conflict():
    request = _make_request()
    redis = AsyncMock()
    redis.get = AsyncMock(
        return_value='{"status":"in_flight","fingerprint":"'
        + _request_fingerprint(request, b'{"name":"Example"}')
        + '"}'
    )

    result = await load_idempotent_response(request, redis, user_sub="user-sub")

    assert result is not None
    assert result.status_code == 409
