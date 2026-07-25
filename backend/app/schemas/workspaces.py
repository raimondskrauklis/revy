# backend/app/schemas/workspaces.py
"""Workspace API contracts — TENANCY.md."""
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, Field

from app.constants.enums import WorkspaceStatus


class WorkspaceUpdate(BaseModel):
    name: str = Field(min_length=1, max_length=255)


class WorkspaceResponse(BaseModel):
    id: UUID
    name: str
    slug: str
    status: WorkspaceStatus

    model_config = {"from_attributes": True}
