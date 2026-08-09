# backend/app/services/github_generation_lifecycle.py
"""Review generation lifecycle — authority and supersede helpers (P0).

Trace field contract (manifest keys — wired in P5):
- ``generation_superseded_at`` — ISO timestamp when a review run is superseded
- ``publish_skipped_not_head`` — publish skipped because revision is not PR HEAD

Supersede scope (P2 + PR #89):
- Review runs: ``GitHubReviewRunStatus.superseded``
- Index jobs: ``GitHubIndexJobStatus.failed`` with error ``Superseded by newer run``
- On new revision: older revision review runs + index jobs
- On same HEAD (``@revy review`` or same-SHA ``synchronize``): active review runs + index jobs

Smart-trigger guard (do not supersede / coalesce on these paths):
| Event | Path | Behavior |
| Bot ``@revy review`` comment | ``apply_issue_comment_webhook_event`` | ignored when ``login == revy_bot_login`` |
| ``pull_request_review`` submitted | ``apply_pull_request_review_webhook_event`` | records review only — no pipeline enqueue |
| Publish-driven GitHub API | N/A | no webhook back into supersede hook |
"""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import (
    GitHubIndexJobStatus,
    GitHubReviewRunStatus,
    stored_enum_value,
)
from app.core.logging import get_logger
from app.models.github_index_job import GitHubIndexJobORM
from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
from app.models.github_review_run import GitHubReviewRunORM
from app.services.github_pipeline_trace import (
    finalize_pipeline_github_check_neutral,
    get_pipeline_run_for_review_run,
    get_pipeline_runs_for_index_jobs,
    record_generation_superseded_on_pipeline,
)

logger = get_logger(__name__)

_SUPERSEDED_CHECK_SUMMARY = "Superseded by newer run"

_ACTIVE_REVIEW_RUN_STATUSES = (
    GitHubReviewRunStatus.pending,
    GitHubReviewRunStatus.processing,
)

_ACTIVE_INDEX_JOB_STATUSES = (
    GitHubIndexJobStatus.pending,
    GitHubIndexJobStatus.processing,
)

_SUPERSEDED_INDEX_ERROR = "Superseded by newer run"


@dataclass(frozen=True)
class SupersedeOutcome:
    review_run_ids: list[UUID]
    index_job_ids: list[UUID]


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


async def _mark_review_run_ids_superseded_cas(
    session: AsyncSession,
    run_ids: list[UUID],
    *,
    pull_request_id: UUID | None = None,
    revision_id: UUID | None = None,
) -> list[UUID]:
    superseded_ids: list[UUID] = []
    for run_id in run_ids:
        result = await session.execute(
            update(GitHubReviewRunORM)
            .where(
                GitHubReviewRunORM.id == run_id,
                GitHubReviewRunORM.status.in_(_ACTIVE_REVIEW_RUN_STATUSES),
            )
            .values(status=GitHubReviewRunStatus.superseded)
        )
        if result.rowcount == 0:
            continue
        superseded_ids.append(run_id)
        logger.info(
            "generation_superseded",
            extra={
                "review_run_id": str(run_id),
                "revision_id": str(revision_id) if revision_id is not None else None,
                "pull_request_id": str(pull_request_id) if pull_request_id is not None else None,
            },
        )
    if superseded_ids:
        await session.flush()
    return superseded_ids


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

    run_ids = list(
        await session.scalars(
            select(GitHubReviewRunORM.id).where(
                GitHubReviewRunORM.revision_id.in_(older_revision_ids),
                GitHubReviewRunORM.status.in_(_ACTIVE_REVIEW_RUN_STATUSES),
            )
        )
    )
    return await _mark_review_run_ids_superseded_cas(
        session,
        run_ids,
        pull_request_id=pull_request_id,
    )


async def mark_active_review_runs_superseded_for_revision(
    session: AsyncSession,
    *,
    revision_id: UUID,
) -> list[UUID]:
    """Mark pending/processing review runs on ``revision_id`` superseded (command vs autostart)."""
    revision = await session.get(GitHubPullRequestRevisionORM, revision_id)
    if revision is None:
        return []

    run_ids = list(
        await session.scalars(
            select(GitHubReviewRunORM.id).where(
                GitHubReviewRunORM.revision_id == revision_id,
                GitHubReviewRunORM.status.in_(_ACTIVE_REVIEW_RUN_STATUSES),
            )
        )
    )
    return await _mark_review_run_ids_superseded_cas(
        session,
        run_ids,
        pull_request_id=revision.pull_request_id,
        revision_id=revision_id,
    )


async def finalize_pipeline_checks_for_superseded_review_runs(
    session: AsyncSession,
    *,
    review_run_ids: list[UUID],
) -> None:
    for review_run_id in review_run_ids:
        await record_generation_superseded_on_pipeline(session, review_run_id=review_run_id)
        pipeline_run = await get_pipeline_run_for_review_run(session, review_run_id=review_run_id)
        if pipeline_run is not None:
            await finalize_pipeline_github_check_neutral(
                session,
                pipeline_run_id=pipeline_run.id,
                summary=_SUPERSEDED_CHECK_SUMMARY,
            )


async def _mark_index_job_ids_superseded_cas(
    session: AsyncSession,
    job_ids: list[UUID],
    *,
    revision_id: UUID | None = None,
) -> list[UUID]:
    """CAS pending/processing index jobs to terminal ``failed`` (RG-Q12 — no ``superseded`` enum)."""
    if not job_ids:
        return []

    result = await session.execute(
        update(GitHubIndexJobORM)
        .where(
            GitHubIndexJobORM.id.in_(job_ids),
            GitHubIndexJobORM.status.in_(_ACTIVE_INDEX_JOB_STATUSES),
        )
        .values(
            status=GitHubIndexJobStatus.failed,
            error_message=_SUPERSEDED_INDEX_ERROR,
        )
        .returning(GitHubIndexJobORM.id)
    )
    superseded_ids = list(result.scalars().all())
    for job_id in superseded_ids:
        logger.info(
            "index_job_superseded",
            extra={
                "index_job_id": str(job_id),
                "revision_id": str(revision_id) if revision_id is not None else None,
            },
        )
    if superseded_ids:
        await session.flush()
    return superseded_ids


async def mark_index_jobs_superseded_for_pull_request(
    session: AsyncSession,
    *,
    pull_request_id: UUID,
    keep_revision_id: UUID,
) -> list[UUID]:
    """Mark pending/processing index jobs on older revisions superseded; keep ``keep_revision_id``."""
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

    job_ids = list(
        await session.scalars(
            select(GitHubIndexJobORM.id).where(
                GitHubIndexJobORM.revision_id.in_(older_revision_ids),
                GitHubIndexJobORM.status.in_(_ACTIVE_INDEX_JOB_STATUSES),
            )
        )
    )
    return await _mark_index_job_ids_superseded_cas(session, job_ids)


async def mark_active_index_jobs_superseded_for_revision(
    session: AsyncSession,
    *,
    revision_id: UUID,
) -> list[UUID]:
    """Mark pending/processing index jobs on ``revision_id`` superseded (command vs autostart)."""
    job_ids = list(
        await session.scalars(
            select(GitHubIndexJobORM.id).where(
                GitHubIndexJobORM.revision_id == revision_id,
                GitHubIndexJobORM.status.in_(_ACTIVE_INDEX_JOB_STATUSES),
            )
        )
    )
    return await _mark_index_job_ids_superseded_cas(session, job_ids, revision_id=revision_id)


async def finalize_pipeline_checks_for_superseded_index_jobs(
    session: AsyncSession,
    *,
    index_job_ids: list[UUID],
) -> None:
    pipeline_runs_by_job_id = await get_pipeline_runs_for_index_jobs(
        session,
        index_job_ids=index_job_ids,
    )
    for index_job_id in index_job_ids:
        pipeline_run = pipeline_runs_by_job_id.get(index_job_id)
        if pipeline_run is None:
            continue
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
) -> SupersedeOutcome:
    """On synchronize: supersede in-flight runs on older revisions and neutralize G10 checks."""
    superseded_review_ids = await mark_review_runs_superseded_for_pull_request(
        session,
        pull_request_id=pull_request_id,
        keep_revision_id=keep_revision_id,
    )
    superseded_index_ids = await mark_index_jobs_superseded_for_pull_request(
        session,
        pull_request_id=pull_request_id,
        keep_revision_id=keep_revision_id,
    )
    await finalize_pipeline_checks_for_superseded_review_runs(
        session,
        review_run_ids=superseded_review_ids,
    )
    await finalize_pipeline_checks_for_superseded_index_jobs(
        session,
        index_job_ids=superseded_index_ids,
    )
    return SupersedeOutcome(
        review_run_ids=superseded_review_ids,
        index_job_ids=superseded_index_ids,
    )


async def supersede_active_generations_for_revision(
    session: AsyncSession,
    *,
    revision_id: UUID,
) -> SupersedeOutcome:
    """On command enqueue or same-SHA synchronize: supersede in-flight on the HEAD revision."""
    superseded_review_ids = await mark_active_review_runs_superseded_for_revision(
        session,
        revision_id=revision_id,
    )
    superseded_index_ids = await mark_active_index_jobs_superseded_for_revision(
        session,
        revision_id=revision_id,
    )
    await finalize_pipeline_checks_for_superseded_review_runs(
        session,
        review_run_ids=superseded_review_ids,
    )
    await finalize_pipeline_checks_for_superseded_index_jobs(
        session,
        index_job_ids=superseded_index_ids,
    )
    return SupersedeOutcome(
        review_run_ids=superseded_review_ids,
        index_job_ids=superseded_index_ids,
    )
