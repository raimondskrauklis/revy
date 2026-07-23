# backend/app/schemas/me.py
"""GET /api/v1/me response — docs/backend/ME_ENDPOINT.md."""
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from app.constants.enums import AppRole, PlatformRole, UserStatus


class MeMembership(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    workspace_id: UUID
    workspace_name: str
    workspace_slug: str
    role: AppRole


class MeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str | None
    status: UserStatus
    platform_role: PlatformRole | None
    workspace_id: UUID | None
    role: AppRole | None
    memberships: list[MeMembership]


class SetActiveWorkspaceRequest(BaseModel):
    workspace_id: UUID
