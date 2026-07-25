# backend/app/api/v1/admin/settings.py
"""Platform settings (read-only) — super_admin only."""
from typing import Annotated

from fastapi import APIRouter, Depends

from app.core.auth import CurrentUser, require_impersonation_allowed, require_super_admin
from app.core.config import settings
from app.schemas.admin import AdminSettingsResponse
from app.schemas.common import SuccessResponse

router = APIRouter(prefix="/settings", tags=["admin-settings"])


@router.get("", response_model=SuccessResponse[AdminSettingsResponse])
async def get_settings(
    _admin: Annotated[CurrentUser, Depends(require_super_admin())],
    _allowed: Annotated[CurrentUser, Depends(require_impersonation_allowed())],
) -> SuccessResponse[AdminSettingsResponse]:
    return SuccessResponse(
        data=AdminSettingsResponse(
            registration_require_admin_approval=settings.registration_require_admin_approval,
            registration_require_profile_form=settings.registration_require_profile_form,
        )
    )
