# backend/app/schemas/invitations.py
"""Invitation API contracts — INVITATIONS.md (P1 table + routes)."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.constants.enums import AppRole, InvitationStatus


class InvitationCreate(BaseModel):
    email: str = Field(min_length=3, max_length=320)
    role: AppRole = AppRole.viewer


class InvitationAcceptRequest(BaseModel):
    token: str = Field(min_length=8)


class InvitationResponse(BaseModel):
    email: str
    role: str
    token: str
    expires_at: str
    invited_by_user_id: str
    workspace_id: str
    status: InvitationStatus = InvitationStatus.pending


class InvitationListItem(BaseModel):
    id: UUID
    email: str
    role: AppRole
    status: InvitationStatus
    expires_at: datetime
    created_at: datetime

    model_config = {"from_attributes": True}
