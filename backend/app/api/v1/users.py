# backend/app/api/v1/users.py
"""User registration routes — USER_REGISTRATION.md."""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.database import get_db
from app.core.exceptions import ForbiddenError
from app.schemas.common import SuccessResponse
from app.schemas.me import MeResponse
from app.schemas.users import CompleteProfileRequest
from app.services.onboarding import complete_user_profile
from app.services.users import build_me_response

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/complete-profile", response_model=SuccessResponse[MeResponse])
async def post_complete_profile(
    body: CompleteProfileRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[MeResponse]:
    if current_user.user_id is None:
        raise ForbiddenError(message="User not provisioned")

    user = await complete_user_profile(
        session,
        current_user.user_id,
        full_name=body.full_name,
    )
    await session.commit()
    me = await build_me_response(session, user.id)
    return SuccessResponse(data=me)
