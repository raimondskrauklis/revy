# backend/app/api/v1/workspaces/settings.py
"""Workspace general settings — TENANCY.md."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.database import get_db
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.permissions import Permission, require_permission
from app.core.tenancy import require_same_workspace
from app.models.workspaces import WorkspaceORM
from app.schemas.common import SuccessResponse
from app.schemas.workspaces import WorkspaceResponse, WorkspaceUpdate
from app.services.workspaces import update_workspace

router = APIRouter(tags=["workspaces"])


@router.patch("/{workspace_id}", response_model=SuccessResponse[WorkspaceResponse])
async def patch_workspace(
    workspace_id: UUID,
    body: WorkspaceUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[WorkspaceResponse]:
    require_permission(current_user, Permission.admin_users)
    require_same_workspace(current_user, workspace_id)
    if current_user.user_id is None:
        raise ForbiddenError(message="User not provisioned")

    workspace = await session.get(WorkspaceORM, workspace_id)
    if workspace is None:
        raise NotFoundError("Workspace not found")

    updated = await update_workspace(
        session,
        workspace_id=workspace_id,
        name=body.name,
        actor_user_id=current_user.user_id,
        impersonator_user_id=current_user.impersonator_user_id,
    )
    await session.commit()
    return SuccessResponse(data=WorkspaceResponse.model_validate(updated))
