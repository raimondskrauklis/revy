# backend/app/workers/async_runner.py
"""Run async coroutines in Celery workers — fresh DB engine per task."""
from __future__ import annotations

import asyncio
from collections.abc import Coroutine
from typing import Any, TypeVar

from app.core import database

T = TypeVar("T")


async def _run_with_engine_teardown(coro: Coroutine[Any, Any, T]) -> T:
    try:
        return await coro
    finally:
        await database.engine.dispose()


def run_worker_async(coro: Coroutine[Any, Any, T]) -> T:
    """Run one async task body; dispose pool on the same loop, then recreate engine."""
    try:
        return asyncio.run(_run_with_engine_teardown(coro))
    finally:
        database._recreate_async_engine()
