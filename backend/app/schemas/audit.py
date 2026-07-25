# backend/app/schemas/audit.py
"""Audit log internal contracts — AUDIT.md."""
from __future__ import annotations

from datetime import datetime
from typing import Any, TypedDict
from uuid import UUID

from pydantic import BaseModel


class AuditLogRecord(TypedDict, total=False):
    actor_user_id: UUID
    impersonator_user_id: UUID | None
    workspace_id: UUID | None
    action: str
    resource_type: str | None
    resource_id: str | None
    metadata: dict[str, Any]


class AuditListItem(BaseModel):
    id: UUID
    created_at: datetime
    action: str
    resource_type: str | None
    resource_id: str | None
    actor_user_id: UUID
    actor_email: str
    impersonator_user_id: UUID | None = None
    impersonator_email: str | None = None
    metadata: dict[str, Any]
