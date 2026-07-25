# backend/app/api/v1/admin/audit.py
"""Platform audit search — super_admin only."""
from datetime import date
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, require_impersonation_allowed, require_super_admin
from app.core.database import get_db
from app.core.pagination import CursorParams, CursorResponse, get_cursor_params
from app.schemas.admin import PlatformAuditListItem
from app.schemas.common import SuccessResponse
from app.services.audit_service import PlatformAuditFilters, list_platform_audit

router = APIRouter(prefix="/audit", tags=["admin-audit"])


@router.get("", response_model=SuccessResponse[CursorResponse[PlatformAuditListItem]])
async def get_platform_audit(
    _admin: Annotated[CurrentUser, Depends(require_super_admin())],
    _allowed: Annotated[CurrentUser, Depends(require_impersonation_allowed())],
    session: Annotated[AsyncSession, Depends(get_db)],
    params: Annotated[CursorParams, Depends(get_cursor_params)],
    workspace_id: Annotated[UUID | None, Query()] = None,
    actor_user_id: Annotated[UUID | None, Query()] = None,
    action_prefix: Annotated[str | None, Query(max_length=128)] = None,
    created_at_from: Annotated[date | None, Query()] = None,
    created_at_to: Annotated[date | None, Query()] = None,
) -> SuccessResponse[CursorResponse[PlatformAuditListItem]]:
    page = await list_platform_audit(
        session,
        params=params,
        filters=PlatformAuditFilters(
            workspace_id=workspace_id,
            actor_user_id=actor_user_id,
            action_prefix=action_prefix,
            created_at_from=created_at_from,
            created_at_to=created_at_to,
        ),
    )
    return SuccessResponse(data=page)
