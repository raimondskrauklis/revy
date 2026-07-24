# backend/app/api/v1/invitations.py
"""Global invitation actions (accept) — INVITATIONS.md."""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.core.auth import CurrentUser, get_current_user
from app.core.database import get_db
from app.core.exceptions import ForbiddenError
from app.core.idempotency import idempotency_guard
from app.models.users import UserORM
from app.schemas.common import SuccessResponse
from app.schemas.invitations import InvitationAcceptRequest
from app.services.invitations import accept_invitation

router = APIRouter(prefix="/invitations", tags=["invitations"])


@router.post("/accept", response_model=SuccessResponse[dict])
async def post_accept_invitation(
    body: InvitationAcceptRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    idempotent: Annotated[JSONResponse | None, Depends(idempotency_guard)] = None,
) -> SuccessResponse[dict] | JSONResponse:
    if idempotent is not None:
        return idempotent
    if current_user.user_id is None:
        raise ForbiddenError(message="User not provisioned")

    user = await session.get(UserORM, current_user.user_id)
    if user is None:
        raise ForbiddenError(message="User not provisioned")

    membership = await accept_invitation(session, token=body.token, user=user)
    await session.commit()
    return SuccessResponse(
        data={
            "workspace_id": str(membership.workspace_id),
            "role": membership.role,
        }
    )
