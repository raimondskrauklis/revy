# backend/app/schemas/admin.py
"""Platform admin API contracts — W5."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.constants.enums import WorkspaceStatus
from app.schemas.audit import AuditListItem


class AdminWorkspaceListItem(BaseModel):
    id: UUID
    name: str
    slug: str
    status: WorkspaceStatus
    plan: str | None
    member_count: int
    created_at: datetime


class AdminWorkspaceDetail(BaseModel):
    id: UUID
    name: str
    slug: str
    status: WorkspaceStatus
    plan: str | None
    member_count: int
    stripe_customer_id: str | None
    created_at: datetime
    updated_at: datetime


class AdminKpisResponse(BaseModel):
    workspaces_total: int
    workspaces_active: int
    workspaces_suspended: int
    users_active: int
    users_pending_approval: int


class AdminSettingsResponse(BaseModel):
    registration_require_admin_approval: bool
    registration_require_profile_form: bool


class PlatformAuditListItem(AuditListItem):
    workspace_id: UUID | None
