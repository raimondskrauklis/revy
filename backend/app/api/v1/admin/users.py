# backend/app/api/v1/admin/users.py
"""Platform signup queue — USER_REGISTRATION.md Mode B."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.core.auth import CurrentUser, require_impersonation_allowed, require_super_admin
from app.core.database import get_db
from app.core.idempotency import idempotency_guard
from app.schemas.common import SuccessResponse
from app.schemas.me import MeResponse
from app.schemas.users import PendingUserResponse
from app.services.users import (
    approve_pending_user,
    build_me_response,
    list_pending_users,
    reject_pending_user,
)

router = APIRouter(prefix="/users", tags=["admin-users"])


@router.get("/pending", response_model=SuccessResponse[list[PendingUserResponse]])
async def get_pending_users(
    _admin: Annotated[CurrentUser, Depends(require_super_admin())],
    _allowed: Annotated[CurrentUser, Depends(require_impersonation_allowed())],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[list[PendingUserResponse]]:
    users = await list_pending_users(session)
    return SuccessResponse(
        data=[PendingUserResponse.model_validate(user) for user in users],
    )


@router.post("/{user_id}/approve", response_model=SuccessResponse[MeResponse])
async def post_approve_user(
    user_id: UUID,
    _admin: Annotated[CurrentUser, Depends(require_super_admin())],
    _allowed: Annotated[CurrentUser, Depends(require_impersonation_allowed())],
    session: Annotated[AsyncSession, Depends(get_db)],
    idempotent: Annotated[JSONResponse | None, Depends(idempotency_guard)] = None,
) -> SuccessResponse[MeResponse] | JSONResponse:
    if idempotent is not None:
        return idempotent
    user = await approve_pending_user(session, user_id)
    await session.commit()
    me = await build_me_response(session, user.id)
    return SuccessResponse(data=me)


@router.post("/{user_id}/reject", response_model=SuccessResponse[PendingUserResponse])
async def post_reject_user(
    user_id: UUID,
    _admin: Annotated[CurrentUser, Depends(require_super_admin())],
    _allowed: Annotated[CurrentUser, Depends(require_impersonation_allowed())],
    session: Annotated[AsyncSession, Depends(get_db)],
    idempotent: Annotated[JSONResponse | None, Depends(idempotency_guard)] = None,
) -> SuccessResponse[PendingUserResponse] | JSONResponse:
    if idempotent is not None:
        return idempotent
    user = await reject_pending_user(session, user_id)
    await session.commit()
    return SuccessResponse(data=PendingUserResponse.model_validate(user))
