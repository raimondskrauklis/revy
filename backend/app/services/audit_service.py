# backend/app/services/audit_service.py
"""Audit log writes — AUDIT.md."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.audit_log import AuditLogORM


async def record_audit(
    session: AsyncSession,
    *,
    actor_user_id: UUID,
    workspace_id: UUID | None,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    impersonator_user_id: UUID | None = None,
) -> AuditLogORM:
    row = AuditLogORM(
        actor_user_id=actor_user_id,
        impersonator_user_id=impersonator_user_id,
        workspace_id=workspace_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata_json=metadata or {},
    )
    session.add(row)
    await session.flush()
    return row
