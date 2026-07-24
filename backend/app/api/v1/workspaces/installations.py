# backend/app/api/v1/workspaces/installations.py
"""Workspace GitHub installations — REVY_PRODUCT_SLICE.md."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.core.auth import CurrentUser, get_current_user
from app.core.database import get_db
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.idempotency import idempotency_guard
from app.core.pagination import CursorParams, CursorResponse, get_cursor_params
from app.core.permissions import Permission, require_permission
from app.core.tenancy import require_same_workspace
from app.models.workspaces import WorkspaceORM
from app.schemas.common import SuccessResponse
from app.schemas.github_installation import GitHubInstallationCreate, GitHubInstallationResponse
from app.services.github_installations import create_github_installation, list_github_installations

router = APIRouter(prefix="/{workspace_id}/installations", tags=["github-installations"])


@router.get("", response_model=SuccessResponse[CursorResponse[GitHubInstallationResponse]])
async def get_workspace_installations(
    workspace_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    params: Annotated[CursorParams, Depends(get_cursor_params)],
) -> SuccessResponse[CursorResponse[GitHubInstallationResponse]]:
    require_permission(current_user, Permission.items_view)
    require_same_workspace(current_user, workspace_id)

    page = await list_github_installations(session, workspace_id=workspace_id, params=params)
    return SuccessResponse(data=page)


@router.post(
    "",
    response_model=SuccessResponse[GitHubInstallationResponse],
    status_code=status.HTTP_201_CREATED,
)
async def post_workspace_installation(
    workspace_id: UUID,
    body: GitHubInstallationCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    idempotent: Annotated[JSONResponse | None, Depends(idempotency_guard)] = None,
) -> SuccessResponse[GitHubInstallationResponse] | JSONResponse:
    if idempotent is not None:
        return idempotent

    require_permission(current_user, Permission.admin_users)
    require_same_workspace(current_user, workspace_id)
    if current_user.user_id is None:
        raise ForbiddenError(message="User not provisioned")

    workspace = await session.get(WorkspaceORM, workspace_id)
    if workspace is None:
        raise NotFoundError("Workspace not found")

    installation = await create_github_installation(
        session,
        workspace_id=workspace_id,
        payload=body,
    )
    await session.commit()
    return SuccessResponse(data=GitHubInstallationResponse.model_validate(installation))
