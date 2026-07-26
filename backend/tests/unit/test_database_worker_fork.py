# backend/tests/unit/test_database_worker_fork.py
"""Celery prefork — async engine must be recreated per worker child."""
import asyncio

from app.core import database


def test_reset_async_engine_for_fork_replaces_engine_and_session_factory() -> None:
    old_engine = database.engine
    old_factory = database.AsyncSessionLocal

    database.reset_async_engine_for_fork()

    assert database.engine is not old_engine
    assert database.AsyncSessionLocal is not old_factory

    asyncio.run(database.engine.dispose())
