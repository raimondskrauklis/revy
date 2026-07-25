# backend/app/api/v1/admin/impersonation.py
"""Platform impersonation — super_admin only."""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, require_impersonation_allowed, require_super_admin
from app.core.database import get_db
from app.core.exceptions import UnauthorizedError
from app.schemas.common import SuccessResponse
from app.schemas.impersonation import ActiveImpersonationResponse, StartImpersonationRequest
from app.services.impersonation import (
    get_active_impersonation_status,
    start_impersonation,
    stop_impersonation,
)

router = APIRouter(prefix="/impersonation", tags=["admin-impersonation"])


@router.post("/start", response_model=SuccessResponse[ActiveImpersonationResponse])
async def post_start_impersonation(
    body: StartImpersonationRequest,
    admin: Annotated[CurrentUser, Depends(require_super_admin())],
    _allowed: Annotated[CurrentUser, Depends(require_impersonation_allowed())],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[ActiveImpersonationResponse]:
    if admin.actor_user_id is None:
        raise UnauthorizedError("User not provisioned")

    status = await start_impersonation(
        session,
        actor_user_id=admin.actor_user_id,
        target_user_id=body.user_id,
        reason=body.reason,
    )
    await session.commit()
    return SuccessResponse(data=status)


@router.post("/stop", response_model=SuccessResponse[ActiveImpersonationResponse])
async def post_stop_impersonation(
    admin: Annotated[CurrentUser, Depends(require_super_admin())],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[ActiveImpersonationResponse]:
    if admin.actor_user_id is None:
        raise UnauthorizedError("User not provisioned")

    status = await stop_impersonation(session, actor_user_id=admin.actor_user_id)
    await session.commit()
    return SuccessResponse(data=status)


@router.get("/active", response_model=SuccessResponse[ActiveImpersonationResponse])
async def get_active_impersonation(
    admin: Annotated[CurrentUser, Depends(require_super_admin())],
    _allowed: Annotated[CurrentUser, Depends(require_impersonation_allowed())],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[ActiveImpersonationResponse]:
    if admin.actor_user_id is None:
        raise UnauthorizedError("User not provisioned")

    status = await get_active_impersonation_status(session, actor_user_id=admin.actor_user_id)
    return SuccessResponse(data=status)
