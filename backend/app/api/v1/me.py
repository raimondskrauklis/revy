# backend/app/api/v1/me.py
"""Current user profile — docs/backend/ME_ENDPOINT.md."""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.database import get_db
from app.core.exceptions import ForbiddenError
from app.schemas.common import SuccessResponse
from app.schemas.me import MeResponse, SetActiveWorkspaceRequest
from app.services.users import build_me_response, set_active_workspace

router = APIRouter(prefix="/me", tags=["me"])


@router.get("", response_model=SuccessResponse[MeResponse])
async def get_me(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[MeResponse]:
    if current_user.user_id is None:
        raise ForbiddenError(message="User not provisioned")
    me = await build_me_response(session, current_user.user_id)
    if current_user.workspace_id is not None:
        me = me.model_copy(
            update={
                "workspace_id": current_user.workspace_id,
                "role": current_user.role,
            }
        )
    return SuccessResponse(data=me)


@router.patch("/workspace", response_model=SuccessResponse[MeResponse])
async def patch_active_workspace(
    body: SetActiveWorkspaceRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[MeResponse]:
    if current_user.user_id is None:
        raise ForbiddenError(message="User not provisioned")
    me = await set_active_workspace(
        session,
        user_id=current_user.user_id,
        workspace_id=body.workspace_id,
    )
    await session.commit()
    return SuccessResponse(data=me)
