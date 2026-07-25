# backend/app/api/v1/workspaces/lifecycle.py
"""Workspace lifecycle — leave and delete."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user, require_impersonation_allowed
from app.core.database import get_db
from app.core.exceptions import ForbiddenError
from app.core.permissions import Permission, require_permission
from app.core.tenancy import require_same_workspace
from app.schemas.lifecycle import DeleteWorkspaceRequest
from app.services.account_lifecycle import delete_workspace, leave_workspace

router = APIRouter(tags=["workspaces"])


@router.post("/{workspace_id}/leave", status_code=status.HTTP_204_NO_CONTENT)
async def post_leave_workspace(
    workspace_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    _allowed: Annotated[CurrentUser, Depends(require_impersonation_allowed())],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    require_same_workspace(current_user, workspace_id)
    if current_user.user_id is None:
        raise ForbiddenError(message="User not provisioned")

    await leave_workspace(
        session,
        workspace_id=workspace_id,
        user_id=current_user.user_id,
        impersonator_user_id=current_user.impersonator_user_id,
    )
    await session.commit()


@router.delete("/{workspace_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace_route(
    workspace_id: UUID,
    body: DeleteWorkspaceRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    _allowed: Annotated[CurrentUser, Depends(require_impersonation_allowed())],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    require_permission(current_user, Permission.admin_users)
    require_same_workspace(current_user, workspace_id)
    if current_user.user_id is None:
        raise ForbiddenError(message="User not provisioned")

    await delete_workspace(
        session,
        workspace_id=workspace_id,
        confirm_slug=body.confirm_slug,
        actor_user_id=current_user.user_id,
        impersonator_user_id=current_user.impersonator_user_id,
    )
    await session.commit()
