# backend/app/services/review_pipeline.py
"""Review pipeline orchestration — R8 autostart and @revy review."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import (
    GitHubIndexJobStatus,
    GitHubIndexJobTriggerSource,
    GitHubPullRequestState,
    GitHubReviewRunStatus,
)
from app.core.config import settings
from app.core.exceptions import ConflictError, ServiceUnavailableError
from app.core.logging import get_logger
from app.models.github_index_job import GitHubIndexJobORM
from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
from app.models.github_review_run import GitHubReviewRunORM
from app.models.workspaces import WorkspaceORM
from app.services.github_indexing import index_job_in_progress
from app.services.github_review import create_review_run

logger = get_logger(__name__)

_PIPELINE_TRIGGERS = frozenset({
    GitHubIndexJobTriggerSource.autostart,
    GitHubIndexJobTriggerSource.command,
})


async def resolve_pending_index_job_id(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    revision_id: UUID,
) -> UUID | None:
    return await session.scalar(
        select(GitHubIndexJobORM.id)
        .where(
            GitHubIndexJobORM.workspace_id == workspace_id,
            GitHubIndexJobORM.revision_id == revision_id,
            GitHubIndexJobORM.status == GitHubIndexJobStatus.pending,
        )
        .limit(1)
    )


async def resolve_pending_review_run_id(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    revision_id: UUID,
) -> UUID | None:
    return await session.scalar(
        select(GitHubReviewRunORM.id)
        .where(
            GitHubReviewRunORM.workspace_id == workspace_id,
            GitHubReviewRunORM.revision_id == revision_id,
            GitHubReviewRunORM.status == GitHubReviewRunStatus.pending,
        )
        .limit(1)
    )


async def review_job_in_progress(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    revision_id: UUID,
) -> bool:
    existing = await session.scalar(
        select(GitHubReviewRunORM.id)
        .where(
            GitHubReviewRunORM.workspace_id == workspace_id,
            GitHubReviewRunORM.revision_id == revision_id,
            GitHubReviewRunORM.status.in_(
                (GitHubReviewRunStatus.pending, GitHubReviewRunStatus.processing),
            ),
        )
        .limit(1)
    )
    return existing is not None


def pipeline_prerequisites_met() -> bool:
    return (
        settings.github_api_enabled
        and settings.embeddings_enabled
        and settings.llm_enabled
    )


async def maybe_enqueue_pipeline_for_revision(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    revision_id: UUID,
    trigger: GitHubIndexJobTriggerSource,
) -> UUID | None:
    if trigger not in _PIPELINE_TRIGGERS:
        raise ValueError(f"unsupported pipeline trigger: {trigger}")

    revision = await session.get(GitHubPullRequestRevisionORM, revision_id)
    if revision is None:
        logger.warning(
            "pipeline_revision_not_found",
            extra={"revision_id": str(revision_id)},
        )
        return None

    pull_request = await session.get(GitHubPullRequestORM, revision.pull_request_id)
    if pull_request is None or pull_request.workspace_id != workspace_id:
        logger.warning(
            "pipeline_pull_request_not_found",
            extra={"revision_id": str(revision_id), "workspace_id": str(workspace_id)},
        )
        return None

    if pull_request.is_draft or pull_request.state != GitHubPullRequestState.open:
        logger.info(
            "pipeline_pr_not_reviewable_skipped",
            extra={
                "workspace_id": str(workspace_id),
                "revision_id": str(revision_id),
                "trigger": trigger.value,
                "is_draft": pull_request.is_draft,
                "state": pull_request.state.value,
            },
        )
        return None

    workspace = await session.get(WorkspaceORM, workspace_id)
    if workspace is None:
        logger.warning(
            "pipeline_workspace_not_found",
            extra={"workspace_id": str(workspace_id)},
        )
        return None

    if trigger == GitHubIndexJobTriggerSource.autostart and not workspace.review_autostart_enabled:
        logger.info(
            "pipeline_autostart_disabled",
            extra={"workspace_id": str(workspace_id), "revision_id": str(revision_id)},
        )
        return None

    if not pipeline_prerequisites_met():
        logger.info(
            "pipeline_prerequisites_missing",
            extra={"workspace_id": str(workspace_id), "revision_id": str(revision_id)},
        )
        return None

    pending_job_id = await resolve_pending_index_job_id(
        session,
        workspace_id=workspace_id,
        revision_id=revision_id,
    )
    if pending_job_id is not None:
        return pending_job_id

    if await index_job_in_progress(
        session,
        workspace_id=workspace_id,
        revision_id=revision_id,
    ):
        logger.info(
            "pipeline_index_in_progress",
            extra={"workspace_id": str(workspace_id), "revision_id": str(revision_id)},
        )
        return None

    if await review_job_in_progress(
        session,
        workspace_id=workspace_id,
        revision_id=revision_id,
    ):
        logger.info(
            "pipeline_review_in_progress",
            extra={"workspace_id": str(workspace_id), "revision_id": str(revision_id)},
        )
        return None

    job = GitHubIndexJobORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubIndexJobStatus.pending,
        trigger_source=trigger,
    )
    session.add(job)
    await session.flush()
    return job.id


async def prepare_review_after_index(
    session: AsyncSession,
    job: GitHubIndexJobORM,
) -> UUID | None:
    if job.status != GitHubIndexJobStatus.completed:
        return None
    if job.trigger_source not in _PIPELINE_TRIGGERS:
        return None

    pending_review_id = await resolve_pending_review_run_id(
        session,
        workspace_id=job.workspace_id,
        revision_id=job.revision_id,
    )
    if pending_review_id is not None:
        return pending_review_id

    revision = await session.get(GitHubPullRequestRevisionORM, job.revision_id)
    if revision is None:
        return None

    pull_request = await session.get(GitHubPullRequestORM, revision.pull_request_id)
    if pull_request is None:
        return None

    if pull_request.is_draft or pull_request.state != GitHubPullRequestState.open:
        logger.info(
            "pipeline_review_skipped_pr_not_reviewable",
            extra={
                "index_job_id": str(job.id),
                "revision_id": str(job.revision_id),
                "is_draft": pull_request.is_draft,
                "state": pull_request.state.value,
            },
        )
        return None

    try:
        run = await create_review_run(
            session,
            workspace_id=job.workspace_id,
            repository_id=pull_request.repository_id,
            pull_request_id=pull_request.id,
            revision_id=job.revision_id,
        )
    except (ConflictError, ServiceUnavailableError) as exc:
        logger.info(
            "pipeline_review_enqueue_skipped",
            extra={
                "index_job_id": str(job.id),
                "revision_id": str(job.revision_id),
                "reason": getattr(exc, "error_code", type(exc).__name__),
            },
        )
        return None

    return run.id
