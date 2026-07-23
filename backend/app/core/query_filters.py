# backend/app/core/query_filters.py
"""Reusable SQLAlchemy query filters — soft delete, tenancy."""
from __future__ import annotations

from typing import TypeVar

from sqlalchemy import Select
from sqlalchemy.orm.attributes import InstrumentedAttribute

T = TypeVar("T")


def has_soft_delete_column(model: type) -> bool:
    return hasattr(model, "deleted_at")


def active_only(stmt: Select[tuple[T]], model: type) -> Select[tuple[T]]:
    """Filter `deleted_at IS NULL` when model supports soft delete."""
    deleted_at: InstrumentedAttribute | None = getattr(model, "deleted_at", None)
    if deleted_at is None:
        return stmt
    return stmt.where(deleted_at.is_(None))
