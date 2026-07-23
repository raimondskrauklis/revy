# backend/app/core/postgres_uuid.py
"""Allocate primary-key UUIDs via PostgreSQL `uuid_generate_v7()` — see docs/backend/MIGRATIONS.md."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession


async def allocate_uuid_v7(session: AsyncSession) -> UUID:
    """Return one time-ordered UUID from the DB (same as ORM `server_default`)."""
    value = await session.scalar(select(func.uuid_generate_v7()))
    if value is None:
        raise RuntimeError("uuid_generate_v7() returned NULL")
    return value
