# backend/app/api/v1/workspaces/installations.py
"""Workspace GitHub installations — REVY_PRODUCT_SLICE.md."""
from typing import Annotated
from urllib.parse import urlencode
from uuid import UUID

import httpx
from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.core.auth import CurrentUser, get_current_user
from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import ForbiddenError, NotFoundError, ServiceUnavailableError
from app.core.idempotency import idempotency_guard
from app.core.pagination import CursorParams, CursorResponse, get_cursor_params
from app.core.permissions import Permission, require_permission
from app.core.tenancy import require_same_workspace
from app.models.workspaces import WorkspaceORM
from app.schemas.common import SuccessResponse
from app.schemas.github_installation import (
    GitHubConnectResponse,
    GitHubInstallationCreate,
    GitHubInstallationResponse,
)
from app.services.github_install_state import mint_install_state
from app.services.github_installations import (
    create_github_installation,
    get_github_installation,
    list_github_installations,
    verify_granted_repositories,
)

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


@router.post("/connect", response_model=SuccessResponse[GitHubConnectResponse])
async def post_workspace_installation_connect(
    workspace_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
) -> SuccessResponse[GitHubConnectResponse]:
    require_permission(current_user, Permission.admin_users)
    require_same_workspace(current_user, workspace_id)
    if current_user.user_id is None:
        raise ForbiddenError(message="User not provisioned")

    slug = (settings.github_app_slug or "").strip()
    client_id = (settings.github_client_id or "").strip()
    if not slug or not client_id:
        raise ServiceUnavailableError(
            message="GitHub App is not configured",
            error_code="github_app_not_configured",
        )

    state = mint_install_state(workspace_id=workspace_id, user_id=current_user.user_id)
    install_url = (
        f"https://github.com/apps/{slug}/installations/new?{urlencode({'state': state})}"
    )
    return SuccessResponse(data=GitHubConnectResponse(install_url=install_url))


@router.post(
    "/{installation_id}/verify",
    response_model=SuccessResponse[GitHubInstallationResponse],
)
async def post_workspace_installation_verify(
    workspace_id: UUID,
    installation_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[GitHubInstallationResponse]:
    require_permission(current_user, Permission.admin_users)
    require_same_workspace(current_user, workspace_id)
    if current_user.user_id is None:
        raise ForbiddenError(message="User not provisioned")

    row = await get_github_installation(
        session,
        workspace_id=workspace_id,
        installation_id=installation_id,
    )
    async with httpx.AsyncClient(timeout=30.0) as client:
        await verify_granted_repositories(session, installation=row, client=client)
    await session.commit()
    return SuccessResponse(data=GitHubInstallationResponse.model_validate(row))
