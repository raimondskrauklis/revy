# backend/app/schemas/impersonation.py
"""Impersonation API contracts — W7."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.constants.enums import AppRole, UserStatus


class StartImpersonationRequest(BaseModel):
    user_id: UUID
    reason: str = Field(min_length=10, max_length=2000)


class ActiveImpersonationResponse(BaseModel):
    active: bool
    target_user_id: UUID | None = None
    target_email: str | None = None
    reason: str | None = None
    started_at: datetime | None = None


class AdminWorkspaceMemberListItem(BaseModel):
    user_id: UUID
    email: str
    full_name: str | None
    status: UserStatus
    role: AppRole
    joined_at: datetime
