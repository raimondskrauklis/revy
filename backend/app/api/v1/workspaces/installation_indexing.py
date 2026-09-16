# backend/app/api/v1/workspaces/installation_indexing.py
"""Workspace PR revision indexing — R3."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.core.auth import CurrentUser, get_current_user
from app.core.database import get_db
from app.core.exceptions import ForbiddenError
from app.core.idempotency import idempotency_guard
from app.core.permissions import Permission, require_permission
from app.core.tenancy import require_same_workspace
from app.models.github_index_job import GitHubIndexJobORM
from app.schemas.common import SuccessResponse
from app.schemas.github_indexing import (
    GitHubChunkSearchRequest,
    GitHubChunkSearchResult,
    GitHubCodeChunkListResponse,
    GitHubIndexJobResponse,
    IndexTriggerRequest,
)
from app.services.github_indexing import (
    CHUNK_LIST_DEFAULT_LIMIT,
    CHUNK_LIST_MAX_LIMIT,
    create_index_job,
    enqueue_index_job,
    ensure_revision_access,
    get_latest_index_job,
    list_revision_chunks,
    search_revision_chunks,
)

router = APIRouter(tags=["github-indexing"])


@router.post(
    "/{workspace_id}/repositories/{repository_id}/pull-requests/{pull_request_id}/revisions/{revision_id}/index",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=SuccessResponse[GitHubIndexJobResponse],
)
async def post_index_pull_request_revision(
    workspace_id: UUID,
    repository_id: UUID,
    pull_request_id: UUID,
    revision_id: UUID,
    body: IndexTriggerRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    idempotent: Annotated[JSONResponse | None, Depends(idempotency_guard)] = None,
) -> SuccessResponse[GitHubIndexJobResponse] | JSONResponse:
    if idempotent is not None:
        return idempotent

    require_permission(current_user, Permission.admin_users)
    require_same_workspace(current_user, workspace_id)
    if current_user.user_id is None:
        raise ForbiddenError(message="User not provisioned")

    job = await create_index_job(
        session,
        workspace_id=workspace_id,
        repository_id=repository_id,
        pull_request_id=pull_request_id,
        revision_id=revision_id,
        index_mode=body.mode,
    )
    await session.commit()

    enqueue_index_job(job.id)
    return SuccessResponse(data=GitHubIndexJobResponse.model_validate(job))


@router.get(
    "/{workspace_id}/repositories/{repository_id}/pull-requests/{pull_request_id}/revisions/{revision_id}/index-job",
    response_model=SuccessResponse[GitHubIndexJobResponse | None],
)
async def get_index_job_for_revision(
    workspace_id: UUID,
    repository_id: UUID,
    pull_request_id: UUID,
    revision_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    job_id: Annotated[UUID | None, Query()] = None,
) -> SuccessResponse[GitHubIndexJobResponse | None]:
    require_permission(current_user, Permission.items_view)
    require_same_workspace(current_user, workspace_id)

    await ensure_revision_access(
        session,
        workspace_id=workspace_id,
        repository_id=repository_id,
        pull_request_id=pull_request_id,
        revision_id=revision_id,
    )
    if job_id is not None:
        job = await session.get(GitHubIndexJobORM, job_id)
        if (
            job is None
            or job.workspace_id != workspace_id
            or job.revision_id != revision_id
        ):
            return SuccessResponse(data=None)
        return SuccessResponse(data=GitHubIndexJobResponse.model_validate(job))
    job = await get_latest_index_job(
        session,
        workspace_id=workspace_id,
        revision_id=revision_id,
    )
    if job is None:
        return SuccessResponse(data=None)
    return SuccessResponse(data=GitHubIndexJobResponse.model_validate(job))


@router.get(
    "/{workspace_id}/repositories/{repository_id}/pull-requests/{pull_request_id}/revisions/{revision_id}/chunks",
    response_model=SuccessResponse[GitHubCodeChunkListResponse],
)
async def get_revision_chunks(
    workspace_id: UUID,
    repository_id: UUID,
    pull_request_id: UUID,
    revision_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=CHUNK_LIST_MAX_LIMIT)] = CHUNK_LIST_DEFAULT_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> SuccessResponse[GitHubCodeChunkListResponse]:
    require_permission(current_user, Permission.items_view)
    require_same_workspace(current_user, workspace_id)

    page = await list_revision_chunks(
        session,
        workspace_id=workspace_id,
        repository_id=repository_id,
        pull_request_id=pull_request_id,
        revision_id=revision_id,
        limit=limit,
        offset=offset,
    )
    return SuccessResponse(data=page)


@router.post(
    "/{workspace_id}/repositories/{repository_id}/pull-requests/{pull_request_id}/revisions/{revision_id}/chunks/search",
    response_model=SuccessResponse[list[GitHubChunkSearchResult]],
)
async def post_search_revision_chunks(
    workspace_id: UUID,
    repository_id: UUID,
    pull_request_id: UUID,
    revision_id: UUID,
    body: GitHubChunkSearchRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[list[GitHubChunkSearchResult]]:
    require_permission(current_user, Permission.items_view)
    require_same_workspace(current_user, workspace_id)

    results = await search_revision_chunks(
        session,
        workspace_id=workspace_id,
        repository_id=repository_id,
        pull_request_id=pull_request_id,
        revision_id=revision_id,
        query=body.query,
        top_k=body.top_k,
    )
    return SuccessResponse(data=results)
