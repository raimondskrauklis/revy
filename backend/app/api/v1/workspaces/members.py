# backend/app/api/v1/workspaces/members.py
"""Workspace members — TENANCY.md."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.database import get_db
from app.core.exceptions import ForbiddenError
from app.core.pagination import CursorParams, CursorResponse, get_cursor_params
from app.core.permissions import Permission, require_permission
from app.core.tenancy import require_same_workspace
from app.models.users import UserORM
from app.schemas.common import SuccessResponse
from app.schemas.memberships import MemberCountResponse, MemberListItem, MemberRoleUpdate
from app.services.memberships import count_members, list_members, remove_member, update_member_role

router = APIRouter(prefix="/{workspace_id}/members", tags=["members"])


@router.get("", response_model=SuccessResponse[CursorResponse[MemberListItem]])
async def get_workspace_members(
    workspace_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    params: Annotated[CursorParams, Depends(get_cursor_params)],
) -> SuccessResponse[CursorResponse[MemberListItem]]:
    require_permission(current_user, Permission.items_view)
    require_same_workspace(current_user, workspace_id)

    page = await list_members(session, workspace_id=workspace_id, params=params)
    return SuccessResponse(data=page)


@router.get("/count", response_model=SuccessResponse[MemberCountResponse])
async def get_workspace_member_count(
    workspace_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[MemberCountResponse]:
    require_permission(current_user, Permission.items_view)
    require_same_workspace(current_user, workspace_id)

    total = await count_members(session, workspace_id=workspace_id)
    return SuccessResponse(data=MemberCountResponse(count=total))


@router.patch("/{user_id}", response_model=SuccessResponse[MemberListItem])
async def patch_workspace_member(
    workspace_id: UUID,
    user_id: UUID,
    body: MemberRoleUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[MemberListItem]:
    require_permission(current_user, Permission.admin_users)
    require_same_workspace(current_user, workspace_id)
    if current_user.user_id is None:
        raise ForbiddenError(message="User not provisioned")

    membership = await update_member_role(
        session,
        workspace_id=workspace_id,
        user_id=user_id,
        role=body.role,
        actor_user_id=current_user.user_id,
        impersonator_user_id=current_user.impersonator_user_id,
    )
    await session.commit()

    user = await session.scalar(select(UserORM).where(UserORM.id == user_id))
    return SuccessResponse(
        data=MemberListItem(
            user_id=membership.user_id,
            email=user.email if user else "",
            full_name=user.full_name if user else None,
            role=membership.role,
            created_at=membership.created_at,
        )
    )


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace_member(
    workspace_id: UUID,
    user_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    require_permission(current_user, Permission.admin_users)
    require_same_workspace(current_user, workspace_id)
    if current_user.user_id is None:
        raise ForbiddenError(message="User not provisioned")

    await remove_member(
        session,
        workspace_id=workspace_id,
        user_id=user_id,
        actor_user_id=current_user.user_id,
        impersonator_user_id=current_user.impersonator_user_id,
    )
    await session.commit()
