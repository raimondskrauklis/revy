# backend/app/schemas/me.py
"""GET /api/v1/me response — docs/backend/ME_ENDPOINT.md."""
from __future__ import annotations

from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.constants.enums import AppRole, PlatformRole, UserStatus


class MeMembership(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    workspace_id: UUID
    workspace_name: str
    workspace_slug: str
    role: AppRole


class MeImpersonationInfo(BaseModel):
    active: bool
    actor_user_id: UUID
    target_user_id: UUID
    target_email: str
    reason: str


class MeResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str | None
    status: UserStatus
    platform_role: PlatformRole | None
    workspace_id: UUID | None
    role: AppRole | None
    locale: str
    timezone: str
    memberships: list[MeMembership]
    workspace_plan: str | None = None
    impersonation: MeImpersonationInfo | None = None


class MeUpdate(BaseModel):
    full_name: str | None = Field(default=None, max_length=255)
    locale: str | None = Field(default=None, max_length=16)
    timezone: str | None = Field(default=None, max_length=64)


class SetActiveWorkspaceRequest(BaseModel):
    workspace_id: UUID
