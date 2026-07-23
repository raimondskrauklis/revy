# backend/app/core/rate_limit.py
"""Redis sliding-window rate limiting — docs/backend/RATE_LIMITING.md."""
from __future__ import annotations

import time
from typing import Annotated

from fastapi import Depends, Request
from redis.asyncio import Redis

from app.core.config import settings
from app.core.exceptions import RateLimitedError
from app.core.logging import get_logger

logger = get_logger(__name__)

_redis: Redis | None = None


async def get_redis() -> Redis:
    global _redis
    if _redis is None:
        _redis = Redis.from_url(settings.redis_url, decode_responses=True)
    return _redis


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None


class RateLimiter:
    def __init__(self, *, scope: str, limit: int, window_seconds: int = 60) -> None:
        self.scope = scope
        self.limit = limit
        self.window_seconds = window_seconds

    async def __call__(
        self,
        request: Request,
        redis: Annotated[Redis, Depends(get_redis)],
    ) -> None:
        identifier = request.client.host if request.client else "unknown"
        auth = request.headers.get("Authorization", "")
        if auth.lower().startswith("bearer "):
            identifier = f"user:{hash(auth)}"

        now = int(time.time())
        window_start = now - self.window_seconds
        key = f"ratelimit:{self.scope}:{identifier}:{now // self.window_seconds}"

        pipe = redis.pipeline()
        pipe.zremrangebyscore(key, 0, window_start)
        pipe.zadd(key, {str(now): now})
        pipe.zcard(key)
        pipe.expire(key, self.window_seconds + 1)
        _, _, count, _ = await pipe.execute()

        if int(count) > self.limit:
            logger.info(
                "rate_limited",
                extra={
                    "scope": self.scope,
                    "path": request.url.path,
                    "operation": "rate_limit",
                },
            )
            raise RateLimitedError(
                message="Too many requests",
                details={"retry_after_seconds": self.window_seconds},
            )


rate_limit_auth = RateLimiter(scope="auth", limit=30, window_seconds=60)
rate_limit_api = RateLimiter(scope="api", limit=120, window_seconds=60)
