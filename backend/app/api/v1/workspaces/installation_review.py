# backend/app/api/v1/workspaces/installation_review.py
"""Workspace PR revision review — R4."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.core.auth import CurrentUser, get_current_user
from app.core.database import get_db
from app.core.exceptions import ConflictError, ForbiddenError
from app.core.idempotency import idempotency_guard
from app.core.pagination import CursorParams, CursorResponse, get_cursor_params
from app.core.permissions import Permission, require_permission
from app.core.tenancy import require_same_workspace
from app.schemas.common import SuccessResponse
from app.schemas.github_pipeline import PipelineRunResponse
from app.schemas.github_publish import GitHubPublishJobResponse
from app.schemas.github_review import (
    DismissFindingGroupRequest,
    GitHubFindingListResponse,
    GitHubReviewRunResponse,
    ReconciledFindingResponse,
    ReviewTriggerRequest,
)
from app.services.audit_service import record_audit
from app.services.github_finding_closure import dismiss_finding_group
from app.services.github_finding_reconcile import list_reconciled_finding_groups
from app.services.github_indexing import (
    enqueue_index_job,
    ensure_revision_access,
    prepare_full_index_for_review_profile,
)
from app.services.github_pipeline_trace import get_pipeline_trace_for_review_run
from app.services.github_publish import (
    create_publish_job,
    enqueue_publish_job,
    get_latest_publish_job_for_revision,
)
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

    enqueued_index = await prepare_full_index_for_review_profile(
        session,
        workspace_id=workspace_id,
        repository_id=repository_id,
        pull_request_id=pull_request_id,
        revision_id=revision_id,
        profile=body.profile,
    )
    if enqueued_index is not None:
        await record_audit(
            session,
            actor_user_id=current_user.user_id,
            workspace_id=workspace_id,
            action="index.run_requested",
            resource_type="github_index_job",
            resource_id=str(enqueued_index.id),
            metadata={
                "revision_id": str(revision_id),
                "index_mode": "full",
                "reason": "deep_critical_review",
            },
        )
        await session.commit()
        enqueue_index_job(enqueued_index.id)
        raise ConflictError(
            message="Full-repo index required for deep/critical review; index job enqueued",
            error_code="full_index_required",
        )

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
    "/{workspace_id}/repositories/{repository_id}/pull-requests/{pull_request_id}/revisions/{revision_id}/review-runs/{review_run_id}/pipeline",
    response_model=SuccessResponse[PipelineRunResponse],
)
async def get_review_run_pipeline(
    workspace_id: UUID,
    repository_id: UUID,
    pull_request_id: UUID,
    revision_id: UUID,
    review_run_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[PipelineRunResponse]:
    require_permission(current_user, Permission.items_view)
    require_same_workspace(current_user, workspace_id)

    pipeline = await get_pipeline_trace_for_review_run(
        session,
        workspace_id=workspace_id,
        repository_id=repository_id,
        pull_request_id=pull_request_id,
        revision_id=revision_id,
        review_run_id=review_run_id,
    )
    return SuccessResponse(data=pipeline)


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


@router.get(
    "/{workspace_id}/repositories/{repository_id}/pull-requests/{pull_request_id}/findings/reconciled",
    response_model=SuccessResponse[CursorResponse[ReconciledFindingResponse]],
)
async def get_reconciled_findings(
    workspace_id: UUID,
    repository_id: UUID,
    pull_request_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    params: Annotated[CursorParams, Depends(get_cursor_params)],
) -> SuccessResponse[CursorResponse[ReconciledFindingResponse]]:
    require_permission(current_user, Permission.items_view)
    require_same_workspace(current_user, workspace_id)

    page = await list_reconciled_finding_groups(
        session,
        workspace_id=workspace_id,
        repository_id=repository_id,
        pull_request_id=pull_request_id,
        params=params,
    )
    return SuccessResponse(data=page)


@router.post(
    "/{workspace_id}/repositories/{repository_id}/pull-requests/{pull_request_id}/finding-groups/{group_id}/dismiss",
    response_model=SuccessResponse[ReconciledFindingResponse],
)
async def post_dismiss_finding_group(
    workspace_id: UUID,
    repository_id: UUID,
    pull_request_id: UUID,
    group_id: UUID,
    body: DismissFindingGroupRequest,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[ReconciledFindingResponse]:
    require_permission(current_user, Permission.admin_users)
    require_same_workspace(current_user, workspace_id)
    if current_user.user_id is None:
        raise ForbiddenError(message="User not provisioned")

    group = await dismiss_finding_group(
        session,
        workspace_id=workspace_id,
        repository_id=repository_id,
        pull_request_id=pull_request_id,
        group_id=group_id,
    )

    metadata: dict[str, str] = {"pull_request_id": str(pull_request_id)}
    if body.reason:
        metadata["reason"] = body.reason
    await record_audit(
        session,
        actor_user_id=current_user.user_id,
        workspace_id=workspace_id,
        action="finding_group.dismissed",
        resource_type="github_finding_group",
        resource_id=str(group.id),
        metadata=metadata,
    )

    await session.commit()
    return SuccessResponse(data=ReconciledFindingResponse.model_validate(group))


@router.post(
    "/{workspace_id}/repositories/{repository_id}/pull-requests/{pull_request_id}/revisions/{revision_id}/publish",
    status_code=status.HTTP_202_ACCEPTED,
    response_model=SuccessResponse[GitHubPublishJobResponse],
)
async def post_publish_pull_request_revision(
    workspace_id: UUID,
    repository_id: UUID,
    pull_request_id: UUID,
    revision_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    idempotent: Annotated[JSONResponse | None, Depends(idempotency_guard)] = None,
) -> SuccessResponse[GitHubPublishJobResponse] | JSONResponse:
    if idempotent is not None:
        return idempotent

    require_permission(current_user, Permission.admin_users)
    require_same_workspace(current_user, workspace_id)
    if current_user.user_id is None:
        raise ForbiddenError(message="User not provisioned")

    job = await create_publish_job(
        session,
        workspace_id=workspace_id,
        repository_id=repository_id,
        pull_request_id=pull_request_id,
        revision_id=revision_id,
    )
    await session.commit()

    enqueue_publish_job(job.id)
    return SuccessResponse(data=GitHubPublishJobResponse.model_validate(job))


@router.get(
    "/{workspace_id}/repositories/{repository_id}/pull-requests/{pull_request_id}/revisions/{revision_id}/publish-job",
    response_model=SuccessResponse[GitHubPublishJobResponse | None],
)
async def get_publish_job_for_revision(
    workspace_id: UUID,
    repository_id: UUID,
    pull_request_id: UUID,
    revision_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[GitHubPublishJobResponse | None]:
    require_permission(current_user, Permission.items_view)
    require_same_workspace(current_user, workspace_id)

    await ensure_revision_access(
        session,
        workspace_id=workspace_id,
        repository_id=repository_id,
        pull_request_id=pull_request_id,
        revision_id=revision_id,
    )
    job = await get_latest_publish_job_for_revision(
        session,
        workspace_id=workspace_id,
        revision_id=revision_id,
    )
    if job is None:
        return SuccessResponse(data=None)
    return SuccessResponse(data=GitHubPublishJobResponse.model_validate(job))
