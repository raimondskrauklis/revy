# backend/app/schemas/items.py
"""Item API contracts — separate Create / Update / Response per AGENT_PATTERNS.md."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.constants.enums import ItemStatus


class ItemCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    status: ItemStatus = ItemStatus.draft


class ItemUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    status: ItemStatus | None = None


class ItemResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    workspace_id: UUID
    name: str
    status: ItemStatus
    created_at: datetime
    updated_at: datetime
    created_by_id: UUID | None = None
    updated_by_id: UUID | None = None
