# backend/app/core/pagination.py
"""Cursor pagination — see docs/backend/API.md."""
from __future__ import annotations

import base64
import json
from datetime import datetime
from typing import Any, Generic, TypeVar
from uuid import UUID

from fastapi import Query
from pydantic import BaseModel, Field

from app.core.config import settings

T = TypeVar("T")


class CursorParams(BaseModel):
    cursor: str | None = None
    limit: int = Field(default=50, ge=1, le=100)


def get_cursor_params(
    cursor: str | None = Query(default=None, description="Opaque cursor from previous page"),
    limit: int = Query(
        default=settings.default_page_limit,
        ge=1,
        le=settings.max_page_limit,
        description="Maximum number of results",
    ),
) -> CursorParams:
    return CursorParams(cursor=cursor, limit=limit)


class CursorMeta(BaseModel):
    next_cursor: str | None
    has_next: bool


class CursorResponse(BaseModel, Generic[T]):
    items: list[T]
    cursor: CursorMeta


class InvalidCursorError(ValueError):
    """Raised when a cursor token cannot be decoded."""


def encode_cursor(created_at: datetime, row_id: UUID) -> str:
    payload = {"t": created_at.isoformat(), "id": str(row_id)}
    raw = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def decode_cursor(cursor: str) -> tuple[datetime, UUID]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("utf-8"))
        data = json.loads(raw)
        return datetime.fromisoformat(data["t"]), UUID(data["id"])
    except Exception as exc:
        raise InvalidCursorError("Invalid cursor token") from exc


def encode_cursor_payload(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, default=str, separators=(",", ":")).encode("utf-8")
    return base64.urlsafe_b64encode(raw).decode("utf-8")


def decode_cursor_payload(cursor: str) -> dict[str, Any]:
    try:
        raw = base64.urlsafe_b64decode(cursor.encode("utf-8"))
        data = json.loads(raw)
        if not isinstance(data, dict):
            raise InvalidCursorError("Cursor payload must be an object")
        return data
    except InvalidCursorError:
        raise
    except Exception as exc:
        raise InvalidCursorError("Invalid cursor token") from exc
