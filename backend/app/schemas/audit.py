# backend/app/schemas/audit.py
"""Audit log internal contracts — AUDIT.md."""
from __future__ import annotations

from typing import Any, TypedDict
from uuid import UUID


class AuditLogRecord(TypedDict, total=False):
    actor_user_id: UUID
    impersonator_user_id: UUID | None
    workspace_id: UUID | None
    action: str
    resource_type: str | None
    resource_id: str | None
    metadata: dict[str, Any]
