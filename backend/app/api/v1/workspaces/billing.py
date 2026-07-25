# backend/app/api/v1/workspaces/billing.py
"""Workspace billing — Checkout and Customer Portal sessions."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user, require_impersonation_allowed
from app.core.database import get_db
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.permissions import Permission, require_permission
from app.core.tenancy import require_same_workspace
from app.models.workspaces import WorkspaceORM
from app.schemas.billing import (
    BillingStatus,
    CheckoutSessionRequest,
    CheckoutSessionResponse,
    PortalSessionResponse,
)
from app.schemas.common import SuccessResponse
from app.services.billing import (
    create_checkout_session,
    create_portal_session,
    get_billing_status,
)

router = APIRouter(prefix="/{workspace_id}/billing", tags=["billing"])


@router.get("", response_model=SuccessResponse[BillingStatus])
async def get_workspace_billing(
    workspace_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[BillingStatus]:
    require_permission(current_user, Permission.admin_users)
    require_same_workspace(current_user, workspace_id)

    status = await get_billing_status(session, workspace_id)
    return SuccessResponse(data=status)


@router.post("/checkout-session", response_model=SuccessResponse[CheckoutSessionResponse])
async def post_checkout_session(
    workspace_id: UUID,
    body: CheckoutSessionRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    _allowed: Annotated[CurrentUser, Depends(require_impersonation_allowed())],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[CheckoutSessionResponse]:
    require_permission(current_user, Permission.admin_users)
    require_same_workspace(current_user, workspace_id)
    if current_user.user_id is None:
        raise ForbiddenError(message="User not provisioned")

    workspace = await session.get(WorkspaceORM, workspace_id)
    if workspace is None:
        raise NotFoundError("Workspace not found")

    url = await create_checkout_session(
        session,
        workspace_id=workspace_id,
        plan=body.plan,
        actor_user_id=current_user.user_id,
        actor_email=current_user.email,
        impersonator_user_id=current_user.impersonator_user_id,
    )
    await session.commit()
    return SuccessResponse(data=CheckoutSessionResponse(url=url))


@router.post("/portal-session", response_model=SuccessResponse[PortalSessionResponse])
async def post_portal_session(
    workspace_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    _allowed: Annotated[CurrentUser, Depends(require_impersonation_allowed())],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[PortalSessionResponse]:
    require_permission(current_user, Permission.admin_users)
    require_same_workspace(current_user, workspace_id)
    if current_user.user_id is None:
        raise ForbiddenError(message="User not provisioned")

    workspace = await session.get(WorkspaceORM, workspace_id)
    if workspace is None:
        raise NotFoundError("Workspace not found")

    url = await create_portal_session(
        session,
        workspace_id=workspace_id,
        actor_user_id=current_user.user_id,
        impersonator_user_id=current_user.impersonator_user_id,
    )
    await session.commit()
    return SuccessResponse(data=PortalSessionResponse(url=url))
