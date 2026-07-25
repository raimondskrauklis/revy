# backend/app/api/v1/workspaces/invitations.py
"""Workspace invitations — INVITATIONS.md."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.constants.enums import InvitationStatus
from app.core.auth import CurrentUser, get_current_user
from app.core.database import get_db
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.idempotency import idempotency_guard
from app.core.pagination import CursorParams, CursorResponse, get_cursor_params
from app.core.permissions import Permission, require_permission
from app.core.tenancy import require_same_workspace
from app.models.users import UserORM
from app.models.workspaces import WorkspaceORM
from app.schemas.common import SuccessResponse
from app.schemas.invitations import InvitationCreate, InvitationListItem, InvitationResponse
from app.services.email_dispatch import enqueue_workspace_invitation_email
from app.services.invitations import (
    create_invitation,
    invitation_to_payload,
    list_invitations,
    revoke_invitation,
)

router = APIRouter(prefix="/{workspace_id}/invitations", tags=["invitations"])


@router.get("", response_model=SuccessResponse[CursorResponse[InvitationListItem]])
async def get_workspace_invitations(
    workspace_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    params: Annotated[CursorParams, Depends(get_cursor_params)],
    invitation_status: Annotated[InvitationStatus | None, Query(alias="status")] = InvitationStatus.pending,
) -> SuccessResponse[CursorResponse[InvitationListItem]]:
    require_permission(current_user, Permission.admin_users)
    require_same_workspace(current_user, workspace_id)

    page = await list_invitations(
        session, workspace_id=workspace_id, params=params, status=invitation_status
    )
    return SuccessResponse(data=page)


@router.delete("/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_workspace_invitation(
    workspace_id: UUID,
    invitation_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    require_permission(current_user, Permission.admin_users)
    require_same_workspace(current_user, workspace_id)
    if current_user.user_id is None:
        raise ForbiddenError(message="User not provisioned")

    await revoke_invitation(
        session,
        workspace_id=workspace_id,
        invitation_id=invitation_id,
        actor_user_id=current_user.user_id,
        impersonator_user_id=current_user.impersonator_user_id,
    )
    await session.commit()


@router.post("", response_model=SuccessResponse[InvitationResponse], status_code=status.HTTP_201_CREATED)
async def post_workspace_invitation(
    workspace_id: UUID,
    body: InvitationCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    idempotent: Annotated[JSONResponse | None, Depends(idempotency_guard)] = None,
) -> SuccessResponse[InvitationResponse] | JSONResponse:
    if idempotent is not None:
        return idempotent
    require_permission(current_user, Permission.admin_users)
    require_same_workspace(current_user, workspace_id)
    if current_user.user_id is None:
        raise ForbiddenError(message="User not provisioned")

    workspace = await session.get(WorkspaceORM, workspace_id)
    if workspace is None:
        raise NotFoundError("Workspace not found")

    inviter = await session.get(UserORM, current_user.user_id)
    inviter_name = (inviter.full_name if inviter and inviter.full_name else None) or (
        inviter.email if inviter else current_user.email or "A teammate"
    )

    invitation = await create_invitation(
        session,
        workspace_id=workspace_id,
        email=body.email,
        role=body.role,
        invited_by_user_id=current_user.user_id,
        impersonator_user_id=current_user.impersonator_user_id,
    )
    await session.commit()
    payload = invitation_to_payload(invitation)
    enqueue_workspace_invitation_email(
        to_email=payload["email"],
        inviter_name=inviter_name,
        workspace_name=workspace.name,
        accept_token=payload["token"],
    )
    return SuccessResponse(data=InvitationResponse.model_validate(payload))
