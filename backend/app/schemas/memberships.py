# backend/app/schemas/memberships.py
"""Workspace membership API contracts — TENANCY.md."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.constants.enums import AppRole


class MemberListItem(BaseModel):
    user_id: UUID
    email: str
    full_name: str | None
    role: AppRole
    created_at: datetime


class MemberRoleUpdate(BaseModel):
    role: AppRole


class MemberCountResponse(BaseModel):
    count: int
