# backend/app/api/v1/workspaces/audit.py
"""Workspace audit log — AUDIT.md."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.database import get_db
from app.core.pagination import CursorParams, CursorResponse, get_cursor_params
from app.core.permissions import Permission, require_permission
from app.core.tenancy import require_same_workspace
from app.schemas.audit import AuditListItem
from app.schemas.common import SuccessResponse
from app.services.audit_service import list_workspace_audit

router = APIRouter(prefix="/{workspace_id}/audit", tags=["audit"])


@router.get("", response_model=SuccessResponse[CursorResponse[AuditListItem]])
async def get_workspace_audit(
    workspace_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    params: Annotated[CursorParams, Depends(get_cursor_params)],
) -> SuccessResponse[CursorResponse[AuditListItem]]:
    require_permission(current_user, Permission.items_view)
    require_same_workspace(current_user, workspace_id)

    page = await list_workspace_audit(session, workspace_id=workspace_id, params=params)
    return SuccessResponse(data=page)
