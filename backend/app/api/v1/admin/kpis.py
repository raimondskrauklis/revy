# backend/app/api/v1/admin/kpis.py
"""Platform KPI aggregates — super_admin only."""
from typing import Annotated

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, require_impersonation_allowed, require_super_admin
from app.core.database import get_db
from app.schemas.admin import AdminKpisResponse
from app.schemas.common import SuccessResponse
from app.services.admin_kpis import get_admin_kpis

router = APIRouter(prefix="/kpis", tags=["admin-kpis"])


@router.get("", response_model=SuccessResponse[AdminKpisResponse])
async def get_kpis(
    _admin: Annotated[CurrentUser, Depends(require_super_admin())],
    _allowed: Annotated[CurrentUser, Depends(require_impersonation_allowed())],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[AdminKpisResponse]:
    return SuccessResponse(data=await get_admin_kpis(session))
