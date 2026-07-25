# backend/app/api/v1/admin/workspaces.py
"""Platform workspace directory — super_admin only."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import WorkspaceStatus
from app.core.auth import CurrentUser, require_super_admin
from app.core.database import get_db
from app.core.exceptions import UnauthorizedError
from app.core.pagination import CursorParams, CursorResponse, get_cursor_params
from app.schemas.admin import AdminWorkspaceDetail, AdminWorkspaceListItem
from app.schemas.common import SuccessResponse
from app.services.admin_workspaces import (
    get_workspace_detail,
    list_workspaces,
    suspend_workspace,
    unsuspend_workspace,
)

router = APIRouter(prefix="/workspaces", tags=["admin-workspaces"])


@router.get("", response_model=SuccessResponse[CursorResponse[AdminWorkspaceListItem]])
async def get_admin_workspaces(
    _admin: Annotated[CurrentUser, Depends(require_super_admin())],
    session: Annotated[AsyncSession, Depends(get_db)],
    params: Annotated[CursorParams, Depends(get_cursor_params)],
    status: Annotated[WorkspaceStatus | None, Query()] = None,
    search: Annotated[str | None, Query(max_length=255)] = None,
) -> SuccessResponse[CursorResponse[AdminWorkspaceListItem]]:
    page = await list_workspaces(session, params=params, status=status, search=search)
    return SuccessResponse(data=page)


@router.get("/{workspace_id}", response_model=SuccessResponse[AdminWorkspaceDetail])
async def get_admin_workspace_detail(
    workspace_id: UUID,
    admin: Annotated[CurrentUser, Depends(require_super_admin())],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[AdminWorkspaceDetail]:
    if admin.user_id is None:
        raise UnauthorizedError("User not provisioned")
    detail = await get_workspace_detail(
        session,
        workspace_id=workspace_id,
        actor_user_id=admin.user_id,
    )
    await session.commit()
    return SuccessResponse(data=detail)


@router.post("/{workspace_id}/suspend", response_model=SuccessResponse[AdminWorkspaceDetail])
async def post_suspend_workspace(
    workspace_id: UUID,
    admin: Annotated[CurrentUser, Depends(require_super_admin())],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[AdminWorkspaceDetail]:
    if admin.user_id is None:
        raise UnauthorizedError("User not provisioned")
    detail = await suspend_workspace(
        session,
        workspace_id=workspace_id,
        actor_user_id=admin.user_id,
    )
    await session.commit()
    return SuccessResponse(data=detail)


@router.post("/{workspace_id}/unsuspend", response_model=SuccessResponse[AdminWorkspaceDetail])
async def post_unsuspend_workspace(
    workspace_id: UUID,
    admin: Annotated[CurrentUser, Depends(require_super_admin())],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[AdminWorkspaceDetail]:
    if admin.user_id is None:
        raise UnauthorizedError("User not provisioned")
    detail = await unsuspend_workspace(
        session,
        workspace_id=workspace_id,
        actor_user_id=admin.user_id,
    )
    await session.commit()
    return SuccessResponse(data=detail)
