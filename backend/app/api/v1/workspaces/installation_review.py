# backend/app/api/v1/workspaces/installation_review.py
"""Workspace PR revision review — R4."""
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
from app.schemas.common import SuccessResponse
from app.schemas.github_review import (
    GitHubFindingListResponse,
    GitHubReviewRunResponse,
    ReviewTriggerRequest,
)
from app.services.audit_service import record_audit
from app.services.github_indexing import ensure_revision_access
from app.services.github_review import (
    FINDING_LIST_DEFAULT_LIMIT,
    FINDING_LIST_MAX_LIMIT,
    create_review_run,
    enqueue_review_run,
    get_latest_review_run,
    list_review_findings,
)

router = APIRouter(tags=["github-review"])


@router.post(
    "/{workspace_id}/repositories/{repository_id}/pull-requests/{pull_request_id}/revisions/{revision_id}/review",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=SuccessResponse[GitHubReviewRunResponse],
)
async def post_review_pull_request_revision(
    workspace_id: UUID,
    repository_id: UUID,
    pull_request_id: UUID,
    revision_id: UUID,
    body: ReviewTriggerRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    idempotent: Annotated[JSONResponse | None, Depends(idempotency_guard)] = None,
) -> SuccessResponse[GitHubReviewRunResponse] | JSONResponse:
    if idempotent is not None:
        return idempotent

    require_permission(current_user, Permission.admin_users)
    require_same_workspace(current_user, workspace_id)
    if current_user.user_id is None:
        raise ForbiddenError(message="User not provisioned")

    run = await create_review_run(
        session,
        workspace_id=workspace_id,
        repository_id=repository_id,
        pull_request_id=pull_request_id,
        revision_id=revision_id,
        profile=body.profile,
    )

    await record_audit(
        session,
        actor_user_id=current_user.user_id,
        workspace_id=workspace_id,
        action="review.run_requested",
        resource_type="github_review_run",
        resource_id=str(run.id),
        metadata={
            "revision_id": str(revision_id),
            "pull_request_id": str(pull_request_id),
            "profile": body.profile.value,
        },
    )
    await session.commit()

    enqueue_review_run(run.id, profile=body.profile)
    return SuccessResponse(data=GitHubReviewRunResponse.model_validate(run))


@router.get(
    "/{workspace_id}/repositories/{repository_id}/pull-requests/{pull_request_id}/revisions/{revision_id}/review-run",
    response_model=SuccessResponse[GitHubReviewRunResponse | None],
)
async def get_review_run_for_revision(
    workspace_id: UUID,
    repository_id: UUID,
    pull_request_id: UUID,
    revision_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[GitHubReviewRunResponse | None]:
    require_permission(current_user, Permission.items_view)
    require_same_workspace(current_user, workspace_id)

    await ensure_revision_access(
        session,
        workspace_id=workspace_id,
        repository_id=repository_id,
        pull_request_id=pull_request_id,
        revision_id=revision_id,
    )
    run = await get_latest_review_run(
        session,
        workspace_id=workspace_id,
        revision_id=revision_id,
    )
    if run is None:
        return SuccessResponse(data=None)
    return SuccessResponse(data=GitHubReviewRunResponse.model_validate(run))


@router.get(
    "/{workspace_id}/repositories/{repository_id}/pull-requests/{pull_request_id}/revisions/{revision_id}/findings",
    response_model=SuccessResponse[GitHubFindingListResponse],
)
async def get_review_findings(
    workspace_id: UUID,
    repository_id: UUID,
    pull_request_id: UUID,
    revision_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    limit: Annotated[int, Query(ge=1, le=FINDING_LIST_MAX_LIMIT)] = FINDING_LIST_DEFAULT_LIMIT,
    offset: Annotated[int, Query(ge=0)] = 0,
) -> SuccessResponse[GitHubFindingListResponse]:
    require_permission(current_user, Permission.items_view)
    require_same_workspace(current_user, workspace_id)

    page = await list_review_findings(
        session,
        workspace_id=workspace_id,
        repository_id=repository_id,
        pull_request_id=pull_request_id,
        revision_id=revision_id,
        limit=limit,
        offset=offset,
    )
    return SuccessResponse(data=page)
