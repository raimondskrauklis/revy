# backend/app/services/workspaces.py
"""Workspace settings — TENANCY.md."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.workspaces import WorkspaceORM


async def update_workspace(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    name: str,
) -> WorkspaceORM:
    workspace = await session.get(WorkspaceORM, workspace_id)
    if workspace is None:
        raise NotFoundError("Workspace not found")

    trimmed = name.strip()
    if not trimmed:
        raise ValidationError(message="Name is required", field="name")

    workspace.name = trimmed
    await session.flush()
    return workspace
