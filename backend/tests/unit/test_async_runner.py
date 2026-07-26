# backend/tests/unit/test_async_runner.py
"""Celery worker async runner — per-task DB engine reset."""
import asyncio

from app.core import database
from app.workers.async_runner import run_worker_async


async def _ping_db() -> int:
    async with database.engine.connect() as conn:
        result = await conn.exec_driver_sql("SELECT 1")
        row = result.first()
        return int(row[0]) if row is not None else 0


def test_run_worker_async_resets_engine_between_invocations() -> None:
    first_engine = database.engine
    assert run_worker_async(_ping_db()) == 1
    assert database.engine is not first_engine

    second_engine = database.engine
    assert run_worker_async(_ping_db()) == 1
    assert database.engine is not second_engine

    asyncio.run(database.engine.dispose())
