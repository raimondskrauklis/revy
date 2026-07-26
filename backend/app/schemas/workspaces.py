# backend/app/schemas/workspaces.py
"""Workspace API contracts — TENANCY.md."""
from __future__ import annotations

from typing import Self
from uuid import UUID

from pydantic import BaseModel, Field, model_validator

from app.constants.enums import WorkspaceStatus


class WorkspaceUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    review_autostart_enabled: bool | None = None

    @model_validator(mode="after")
    def require_at_least_one_field(self) -> Self:
        if self.name is None and self.review_autostart_enabled is None:
            raise ValueError("At least one of name or review_autostart_enabled is required")
        return self


class WorkspaceResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    status: WorkspaceStatus
    review_autostart_enabled: bool

    model_config = {"from_attributes": True}
