# backend/app/api/v1/workspaces/installation_repositories.py
"""Workspace installation repositories — R1 repository sync."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.core.auth import CurrentUser, get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import ForbiddenError, ServiceUnavailableError
from app.core.idempotency import idempotency_guard
from app.core.pagination import CursorParams, CursorResponse, get_cursor_params
from app.core.permissions import Permission, require_permission
from app.core.tenancy import require_same_workspace
from app.schemas.common import SuccessResponse
from app.schemas.github_repository import GitHubRepositoryResponse
from app.services.github_repositories import (
    enqueue_installation_repository_sync,
    list_github_repositories,
)

router = APIRouter(tags=["github-repositories"])


@router.get(
    "/{workspace_id}/installations/{installation_id}/repositories",
    response_model=SuccessResponse[CursorResponse[GitHubRepositoryResponse]],
)
async def get_installation_repositories(
    workspace_id: UUID,
    installation_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    params: Annotated[CursorParams, Depends(get_cursor_params)],
) -> SuccessResponse[CursorResponse[GitHubRepositoryResponse]]:
    require_permission(current_user, Permission.items_view)
    require_same_workspace(current_user, workspace_id)

    page = await list_github_repositories(
        session,
        workspace_id=workspace_id,
        installation_id=installation_id,
        params=params,
    )
    return SuccessResponse(data=page)


@router.post(
    "/{workspace_id}/installations/{installation_id}/sync-repositories",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=SuccessResponse[dict[str, str]],
)
async def post_sync_installation_repositories(
    workspace_id: UUID,
    installation_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    idempotent: Annotated[JSONResponse | None, Depends(idempotency_guard)] = None,
) -> SuccessResponse[dict[str, str]] | JSONResponse:
    if idempotent is not None:
        return idempotent

    require_permission(current_user, Permission.admin_users)
    require_same_workspace(current_user, workspace_id)
    if current_user.user_id is None:
        raise ForbiddenError(message="User not provisioned")

    if not settings.github_api_enabled:
        raise ServiceUnavailableError(
            message="GitHub App API is not configured",
            error_code="github_api_disabled",
        )

    from app.services.github_installations import get_github_installation

    await get_github_installation(
        session,
        workspace_id=workspace_id,
        installation_id=installation_id,
    )
    await session.commit()

    enqueue_installation_repository_sync(installation_id)
    return SuccessResponse(data={"status": "queued"})
