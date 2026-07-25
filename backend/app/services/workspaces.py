# backend/app/services/workspaces.py
"""Workspace settings — TENANCY.md."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.workspaces import WorkspaceORM
from app.services.audit_service import record_audit


async def update_workspace(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    name: str,
    actor_user_id: UUID | None = None,
    impersonator_user_id: UUID | None = None,
) -> WorkspaceORM:
    workspace = await session.get(WorkspaceORM, workspace_id)
    if workspace is None:
        raise NotFoundError("Workspace not found")

    trimmed = name.strip()
    if not trimmed:
        raise ValidationError(message="Name is required", field="name")

    old_name = workspace.name
    workspace.name = trimmed
    await session.flush()

    if actor_user_id is not None and old_name != trimmed:
        await record_audit(
            session,
            actor_user_id=actor_user_id,
            impersonator_user_id=impersonator_user_id,
            workspace_id=workspace_id,
            action="workspace.updated",
            resource_type="workspace",
            resource_id=str(workspace_id),
            metadata={"old_name": old_name, "new_name": trimmed},
        )

    return workspace
