# backend/app/services/github_generation_lifecycle.py
"""Review generation lifecycle — authority and supersede helpers (P0).

Trace field contract (manifest keys — wired in P5):
- ``generation_superseded_at`` — ISO timestamp when a review run is superseded
- ``publish_skipped_not_head`` — publish skipped because revision is not PR HEAD

Smart-trigger guard (do not supersede / coalesce on these paths):
| Event | Path | Behavior |
| Bot ``@revy review`` comment | ``apply_issue_comment_webhook_event`` | ignored when ``login == revy_bot_login`` |
| ``pull_request_review`` submitted | ``apply_pull_request_review_webhook_event`` | records review only — no pipeline enqueue |
| Publish-driven GitHub API | N/A | no webhook back into supersede hook |
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import GitHubReviewRunStatus, stored_enum_value
from app.core.logging import get_logger
from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
from app.models.github_review_run import GitHubReviewRunORM
from app.services.github_pipeline_trace import (
    finalize_pipeline_github_check_neutral,
    get_pipeline_run_for_review_run,
)

logger = get_logger(__name__)

_SUPERSEDED_CHECK_SUMMARY = "Superseded by newer commit"

_ACTIVE_REVIEW_RUN_STATUSES = (
    GitHubReviewRunStatus.pending,
    GitHubReviewRunStatus.processing,
)


async def is_authoritative_for_pull_request_head(
    session: AsyncSession,
    *,
    revision_id: UUID,
) -> bool:
    revision = await session.get(GitHubPullRequestRevisionORM, revision_id)
    if revision is None:
        return False
    pull_request = await session.get(GitHubPullRequestORM, revision.pull_request_id)
    if pull_request is None:
        return False
    return revision.head_sha == pull_request.head_sha


def is_review_run_superseded(run: GitHubReviewRunORM) -> bool:
    return stored_enum_value(run.status) == GitHubReviewRunStatus.superseded.value


async def mark_review_runs_superseded_for_pull_request(
    session: AsyncSession,
    *,
    pull_request_id: UUID,
    keep_revision_id: UUID,
) -> list[UUID]:
    """Mark pending/processing review runs on older revisions superseded; keep ``keep_revision_id``."""
    keep_revision = await session.get(GitHubPullRequestRevisionORM, keep_revision_id)
    if keep_revision is None or keep_revision.pull_request_id != pull_request_id:
        return []

    older_revision_ids = list(
        await session.scalars(
            select(GitHubPullRequestRevisionORM.id).where(
                GitHubPullRequestRevisionORM.pull_request_id == pull_request_id,
                GitHubPullRequestRevisionORM.revision_number < keep_revision.revision_number,
            )
        )
    )
    if not older_revision_ids:
        return []

    runs = list(
        await session.scalars(
            select(GitHubReviewRunORM).where(
                GitHubReviewRunORM.revision_id.in_(older_revision_ids),
                GitHubReviewRunORM.status.in_(_ACTIVE_REVIEW_RUN_STATUSES),
            )
        )
    )
    superseded_ids: list[UUID] = []
    for run in runs:
        run.status = GitHubReviewRunStatus.superseded
        superseded_ids.append(run.id)
        logger.info(
            "generation_superseded",
            extra={
                "review_run_id": str(run.id),
                "revision_id": str(run.revision_id),
                "pull_request_id": str(pull_request_id),
            },
        )
    if superseded_ids:
        await session.flush()
    return superseded_ids


async def mark_active_review_runs_superseded_for_revision(
    session: AsyncSession,
    *,
    revision_id: UUID,
) -> list[UUID]:
    """Mark pending/processing review runs on ``revision_id`` superseded (command vs autostart)."""
    revision = await session.get(GitHubPullRequestRevisionORM, revision_id)
    if revision is None:
        return []

    runs = list(
        await session.scalars(
            select(GitHubReviewRunORM).where(
                GitHubReviewRunORM.revision_id == revision_id,
                GitHubReviewRunORM.status.in_(_ACTIVE_REVIEW_RUN_STATUSES),
            )
        )
    )
    superseded_ids: list[UUID] = []
    for run in runs:
        run.status = GitHubReviewRunStatus.superseded
        superseded_ids.append(run.id)
        logger.info(
            "generation_superseded",
            extra={
                "review_run_id": str(run.id),
                "revision_id": str(revision_id),
                "pull_request_id": str(revision.pull_request_id),
            },
        )
    if superseded_ids:
        await session.flush()
    return superseded_ids


async def finalize_pipeline_checks_for_superseded_review_runs(
    session: AsyncSession,
    *,
    review_run_ids: list[UUID],
) -> None:
    for review_run_id in review_run_ids:
        pipeline_run = await get_pipeline_run_for_review_run(session, review_run_id=review_run_id)
        if pipeline_run is not None:
            await finalize_pipeline_github_check_neutral(
                session,
                pipeline_run_id=pipeline_run.id,
                summary=_SUPERSEDED_CHECK_SUMMARY,
            )


async def supersede_stale_generations_for_new_revision(
    session: AsyncSession,
    *,
    pull_request_id: UUID,
    keep_revision_id: UUID,
) -> list[UUID]:
    """On synchronize: supersede in-flight runs on older revisions and neutralize G10 checks."""
    superseded_ids = await mark_review_runs_superseded_for_pull_request(
        session,
        pull_request_id=pull_request_id,
        keep_revision_id=keep_revision_id,
    )
    await finalize_pipeline_checks_for_superseded_review_runs(
        session,
        review_run_ids=superseded_ids,
    )
    return superseded_ids


async def supersede_active_generations_for_revision(
    session: AsyncSession,
    *,
    revision_id: UUID,
) -> list[UUID]:
    """On command enqueue: supersede autostart in-flight on the same HEAD revision."""
    superseded_ids = await mark_active_review_runs_superseded_for_revision(
        session,
        revision_id=revision_id,
    )
    await finalize_pipeline_checks_for_superseded_review_runs(
        session,
        review_run_ids=superseded_ids,
    )
    return superseded_ids
