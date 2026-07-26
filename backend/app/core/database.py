# backend/app/core/database.py
"""Async SQLAlchemy session management — see internal-docs starter-pack docs/backend/DATABASE.md."""
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


def _create_engine() -> AsyncEngine:
    return create_async_engine(
        str(settings.database_url),
        echo=settings.debug,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
    )


def _create_session_factory(bind: AsyncEngine) -> async_sessionmaker[AsyncSession]:
    return async_sessionmaker(
        bind,
        class_=AsyncSession,
        expire_on_commit=False,
        autocommit=False,
        autoflush=False,
    )


engine: AsyncEngine = _create_engine()

AsyncSessionLocal = _create_session_factory(engine)


def _recreate_async_engine() -> None:
    global engine, AsyncSessionLocal
    engine = _create_engine()
    AsyncSessionLocal = _create_session_factory(engine)


def reset_async_engine_for_fork() -> None:
    """Dispose and recreate the async engine after Celery prefork.

    The parent process imports database.py before fork; asyncpg pools must not
    be shared across worker children or asyncio.run() event loops.
    """
    import asyncio

    try:
        asyncio.run(engine.dispose())
    except Exception:
        logger.warning(
            "database_engine_dispose_after_fork_failed",
            exc_info=True,
        )

    _recreate_async_engine()
    logger.info("database_engine_reset_for_worker", extra={"operation": "reset_async_engine_for_fork"})


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_db_context() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def init_db() -> None:
    async with engine.begin() as conn:
        await conn.execute(text("SELECT 1"))
    logger.info("Database connection established", extra={"operation": "init_db"})


async def close_db() -> None:
    await engine.dispose()
    logger.info("Database connections closed", extra={"operation": "close_db"})
