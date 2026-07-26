# backend/app/api/v1/workspaces/installation_pull_requests.py
"""Workspace repository pull requests — R2 PR ingestion."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.database import get_db
from app.core.pagination import CursorParams, CursorResponse, get_cursor_params
from app.core.permissions import Permission, require_permission
from app.core.tenancy import require_same_workspace
from app.schemas.common import SuccessResponse
from app.schemas.github_pull_request import GitHubPullRequestResponse
from app.services.github_pull_requests import get_github_pull_request, list_github_pull_requests

router = APIRouter(tags=["github-pull-requests"])


@router.get(
    "/{workspace_id}/repositories/{repository_id}/pull-requests/{pull_request_id}",
    response_model=SuccessResponse[GitHubPullRequestResponse],
)
async def get_repository_pull_request(
    workspace_id: UUID,
    repository_id: UUID,
    pull_request_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[GitHubPullRequestResponse]:
    require_permission(current_user, Permission.items_view)
    require_same_workspace(current_user, workspace_id)

    pull_request = await get_github_pull_request(
        session,
        workspace_id=workspace_id,
        repository_id=repository_id,
        pull_request_id=pull_request_id,
    )
    return SuccessResponse(data=GitHubPullRequestResponse.model_validate(pull_request))


@router.get(
    "/{workspace_id}/repositories/{repository_id}/pull-requests",
    response_model=SuccessResponse[CursorResponse[GitHubPullRequestResponse]],
)
async def get_repository_pull_requests(
    workspace_id: UUID,
    repository_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    params: Annotated[CursorParams, Depends(get_cursor_params)],
) -> SuccessResponse[CursorResponse[GitHubPullRequestResponse]]:
    require_permission(current_user, Permission.items_view)
    require_same_workspace(current_user, workspace_id)

    page = await list_github_pull_requests(
        session,
        workspace_id=workspace_id,
        repository_id=repository_id,
        params=params,
    )
    return SuccessResponse(data=page)
