# backend/tests/conftest.py
"""Pytest fixtures — extend for integration tests.

Unit tests in tests/unit/ mock AsyncSession and avoid Postgres.
When adding HTTP integration tests, wire fixtures below with TEST_DATABASE_URL.
"""
from __future__ import annotations

import os

import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import reset_revy_llm_provider_alias_logged
from app.core.database import get_db


@pytest.fixture(autouse=True)
def _reset_config_module_flags() -> None:
    reset_revy_llm_provider_alias_logged()


def _test_database_url() -> str | None:
    from app.core.config import settings

    return os.environ.get("TEST_DATABASE_URL") or settings.test_database_url


@pytest.fixture
async def db_session() -> AsyncSession:
    database_url = _test_database_url()
    if not database_url:
        pytest.skip("TEST_DATABASE_URL not configured")

    engine = create_async_engine(database_url, pool_pre_ping=True)
    session_factory = async_sessionmaker(engine, expire_on_commit=False)
    async with session_factory() as session:
        yield session
    await engine.dispose()


@pytest.fixture
async def async_client(db_session: AsyncSession):
    from app.main import app

    async def _override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = _override_get_db
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        yield client
    app.dependency_overrides.clear()
