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
    name: str | None = None,
    review_autostart_enabled: bool | None = None,
    actor_user_id: UUID | None = None,
    impersonator_user_id: UUID | None = None,
) -> WorkspaceORM:
    if name is None and review_autostart_enabled is None:
        raise ValidationError(
            message="At least one of name or review_autostart_enabled is required",
            field="body",
        )

    workspace = await session.get(WorkspaceORM, workspace_id)
    if workspace is None:
        raise NotFoundError("Workspace not found")

    if name is not None:
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

    if review_autostart_enabled is not None:
        old_value = workspace.review_autostart_enabled
        workspace.review_autostart_enabled = review_autostart_enabled
        await session.flush()

        if actor_user_id is not None and old_value != review_autostart_enabled:
            await record_audit(
                session,
                actor_user_id=actor_user_id,
                impersonator_user_id=impersonator_user_id,
                workspace_id=workspace_id,
                action="workspace.review_autostart_updated",
                resource_type="workspace",
                resource_id=str(workspace_id),
                metadata={
                    "old_review_autostart_enabled": old_value,
                    "new_review_autostart_enabled": review_autostart_enabled,
                },
            )

    return workspace
