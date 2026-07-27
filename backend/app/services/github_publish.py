# backend/app/services/github_publish.py
"""GitHub publish pipeline — R6."""
from __future__ import annotations

import time
from uuid import UUID

import httpx
from sqlalchemy import case, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import (
    FindingSeverity,
    GitHubFindingGroupState,
    GitHubPublishJobStatus,
    GitHubReviewRunStatus,
    stored_enum_value,
)
from app.core.config import settings
from app.core.exceptions import ConflictError, NotFoundError, ServiceUnavailableError
from app.core.logging import get_logger
from app.core.worker_retries import WorkerRetryableError, classify_transient_error
from app.integrations import github_api
from app.models.github_finding import GitHubFindingORM
from app.models.github_finding_group import GitHubFindingGroupORM
from app.models.github_installation import GitHubInstallationORM
from app.models.github_publish_job import GitHubPublishJobORM
from app.models.github_pull_request import (
    GitHubPullRequestORM,
    GitHubPullRequestRevisionORM,
)
from app.models.github_repository import GitHubRepositoryORM
from app.models.github_review_run import GitHubReviewRunORM
from app.services.github_generation_lifecycle import is_review_run_superseded
from app.services.github_indexing import ensure_revision_access, get_latest_completed_index_job
from app.services.github_pipeline_trace import (
    finalize_pipeline_github_check_failure,
    finalize_pipeline_github_check_neutral,
    get_pipeline_run_for_review_run,
    link_publish_job_to_pipeline,
    record_publish_pipeline_step,
    resolve_pipeline_github_check_run_id,
)
from app.services.github_publish_formatter import (
    PublishFormatContext,
    build_publish_format_result_async,
)
from app.services.github_suggestion import is_publishable_suggestion

logger = get_logger(__name__)

SUMMARY_ROW_CAP = 50

_PUBLISH_GROUP_SEVERITY_ORDER = case(
    (GitHubFindingGroupORM.severity == FindingSeverity.critical, 0),
    (GitHubFindingGroupORM.severity == FindingSeverity.error, 1),
    (GitHubFindingGroupORM.severity == FindingSeverity.warning, 2),
    else_=3,
)


class PublishJobRetryableError(WorkerRetryableError):
    """Transient publish failure — Celery should retry after persisting progress."""


_SKIP_PUBLISH_NEUTRAL_SUMMARY = "Superseded by newer commit"

_TERMINAL_PUBLISH_JOB_STATUSES = frozenset({
    GitHubPublishJobStatus.completed,
    GitHubPublishJobStatus.failed,
    GitHubPublishJobStatus.skipped_not_head,
    GitHubPublishJobStatus.skipped_superseded,
})


async def _skip_publish_job_at_gate(
    session: AsyncSession,
    job: GitHubPublishJobORM,
    *,
    skip_status: GitHubPublishJobStatus,
    log_event: str,
) -> GitHubPublishJobORM:
    job.status = skip_status
    job.error_message = None
    await session.flush()
    pipeline_run = await get_pipeline_run_for_review_run(session, review_run_id=job.review_run_id)
    if pipeline_run is not None:
        await finalize_pipeline_github_check_neutral(
            session,
            pipeline_run_id=pipeline_run.id,
            summary=_SKIP_PUBLISH_NEUTRAL_SUMMARY,
        )
    logger.info(
        log_event,
        extra={
            "publish_job_id": str(job.id),
            "review_run_id": str(job.review_run_id),
            "revision_id": str(job.revision_id),
            "head_sha": job.head_sha,
        },
    )
    return job


async def mark_publish_job_failed(
    session: AsyncSession,
    *,
    publish_job_id: UUID,
    error_message: str,
) -> None:
    job = await session.get(GitHubPublishJobORM, publish_job_id)
    if job is None:
        return
    if job.status in (GitHubPublishJobStatus.pending, GitHubPublishJobStatus.processing):
        job.status = GitHubPublishJobStatus.failed
        job.error_message = error_message[:2000]
        await session.flush()


async def create_publish_job_for_review_run(
    session: AsyncSession,
    *,
    review_run_id: UUID,
) -> UUID | None:
    """Create a pending publish job under row lock, or None if skipped."""
    run = await session.scalar(
        select(GitHubReviewRunORM)
        .where(GitHubReviewRunORM.id == review_run_id)
        .with_for_update()
    )
    if run is None or run.status != GitHubReviewRunStatus.completed:
        return None
    if is_review_run_superseded(run):
        return None

    pending = await session.scalar(
        select(GitHubPublishJobORM.id)
        .where(
            GitHubPublishJobORM.review_run_id == run.id,
            GitHubPublishJobORM.status.in_(
                (GitHubPublishJobStatus.pending, GitHubPublishJobStatus.processing),
            ),
        )
        .limit(1)
    )
    if pending is not None:
        return None

    revision = await session.get(GitHubPullRequestRevisionORM, run.revision_id)
    if revision is None:
        return None

    job = GitHubPublishJobORM(
        review_run_id=run.id,
        revision_id=run.revision_id,
        workspace_id=run.workspace_id,
        head_sha=revision.head_sha,
        status=GitHubPublishJobStatus.pending,
    )
    session.add(job)
    await session.flush()

    pipeline_run = await get_pipeline_run_for_review_run(session, review_run_id=run.id)
    if pipeline_run is not None:
        await link_publish_job_to_pipeline(
            session,
            pipeline_run=pipeline_run,
            publish_job_id=job.id,
        )
        pipeline_check_id = await resolve_pipeline_github_check_run_id(
            session,
            pipeline_run_id=pipeline_run.id,
        )
        if pipeline_check_id is not None:
            job.github_check_run_id = pipeline_check_id

    return job.id


async def resolve_publish_job_id_for_review_run(
    session: AsyncSession,
    *,
    review_run_id: UUID,
) -> tuple[UUID | None, bool]:
    """Return a publish job id to dispatch, creating one or reusing pending/processing."""
    job_id = await create_publish_job_for_review_run(session, review_run_id=review_run_id)
    if job_id is not None:
        return job_id, True

    existing = await session.scalar(
        select(GitHubPublishJobORM.id)
        .where(
            GitHubPublishJobORM.review_run_id == review_run_id,
            GitHubPublishJobORM.status.in_(
                (GitHubPublishJobStatus.pending, GitHubPublishJobStatus.processing),
            ),
        )
        .limit(1)
    )
    if existing is None:
        return None, False
    return existing, False


def compute_check_conclusion(groups: list[GitHubFindingGroupORM]) -> str:
    """GitHub check conclusion — advisory like Greptile; CI owns merge gates."""
    active = [g for g in groups if g.state == GitHubFindingGroupState.active]
    if not active:
        return "success"
    return "neutral"


def _revy_ui_link(pull_request_id: UUID) -> str:
    base = (settings.app_public_url or "https://app.revy.dev").rstrip("/")
    return f"{base}/reviewer/pull-requests/{pull_request_id}"


def _escape_markdown_table_cell(value: str) -> str:
    """Escape pipe/newline characters so GitHub markdown table rows stay valid."""
    return value.replace("\\", "\\\\").replace("|", "\\|").replace("\r", " ").replace("\n", " ")


def build_summary_markdown(
    *,
    pull_request_id: UUID,
    groups: list[GitHubFindingGroupORM],
) -> str:
    active_all = [g for g in groups if g.state == GitHubFindingGroupState.active]
    active = active_all[:SUMMARY_ROW_CAP]
    lines = [
        "## Revy review summary",
        "",
        f"[Open in Revy]({_revy_ui_link(pull_request_id)})",
        "",
        "| Severity | Category | Title | File |",
        "| --- | --- | --- | --- |",
    ]
    for group in active:
        file_cell = _escape_markdown_table_cell(group.file_path or "—")
        title_cell = _escape_markdown_table_cell(group.title)
        lines.append(
            f"| {stored_enum_value(group.severity)} | {stored_enum_value(group.category)} | {title_cell} | {file_cell} |"
        )
    if len(active_all) > SUMMARY_ROW_CAP:
        lines.append("")
        lines.append(f"_Showing {SUMMARY_ROW_CAP} of {len(active_all)} findings._")
    return "\n".join(lines)


def inline_publish_findings_statement(*, review_run_id: UUID):
    """Findings eligible for inline GitHub comments — active groups only (R5 judge may resolve)."""
    return (
        select(GitHubFindingORM)
        .join(
            GitHubFindingGroupORM,
            GitHubFindingORM.group_id == GitHubFindingGroupORM.id,
        )
        .where(
            GitHubFindingORM.review_run_id == review_run_id,
            GitHubFindingGroupORM.state == GitHubFindingGroupState.active,
            GitHubFindingORM.severity.in_(
                (
                    FindingSeverity.error,
                    FindingSeverity.critical,
                    FindingSeverity.warning,
                    FindingSeverity.info,
                ),
            ),
            GitHubFindingORM.file_path.is_not(None),
            GitHubFindingORM.start_line.is_not(None),
        )
    )


async def get_latest_publish_job_for_revision(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    revision_id: UUID,
) -> GitHubPublishJobORM | None:
    return await session.scalar(
        select(GitHubPublishJobORM)
        .where(
            GitHubPublishJobORM.workspace_id == workspace_id,
            GitHubPublishJobORM.revision_id == revision_id,
        )
        .order_by(GitHubPublishJobORM.created_at.desc())
        .limit(1)
    )


def deserialize_inline_thread_map(raw: object) -> dict[str, int]:
    """Read legacy int or v2 {comment_id, thread_id?} entries into a comment-id map."""
    if not isinstance(raw, dict):
        return {}
    merged: dict[str, int] = {}
    for fingerprint, value in raw.items():
        if not isinstance(fingerprint, str):
            continue
        if isinstance(value, int):
            merged[fingerprint] = value
        elif isinstance(value, dict):
            comment_id = value.get("comment_id")
            if isinstance(comment_id, int):
                merged[fingerprint] = comment_id
    return merged


def serialize_inline_thread_map(
    comment_map: dict[str, int],
    *,
    prior_v2: dict | None = None,
    thread_ids: dict[str, str] | None = None,
) -> dict[str, dict[str, int | str]]:
    """Persist v2 thread-map entries; preserve thread_id from prior_v2 when fingerprint unchanged."""
    prior = prior_v2 if isinstance(prior_v2, dict) else {}
    extra_thread_ids = thread_ids if isinstance(thread_ids, dict) else {}
    result: dict[str, dict[str, int | str]] = {}
    for fingerprint, comment_id in comment_map.items():
        entry: dict[str, int | str] = {"comment_id": comment_id}
        if fingerprint in extra_thread_ids:
            entry["thread_id"] = extra_thread_ids[fingerprint]
        else:
            prior_entry = prior.get(fingerprint)
            if isinstance(prior_entry, dict):
                prior_comment_id = prior_entry.get("comment_id")
                thread_id = prior_entry.get("thread_id")
                if (
                    prior_comment_id == comment_id
                    and isinstance(thread_id, str)
                    and thread_id
                ):
                    entry["thread_id"] = thread_id
        result[fingerprint] = entry
    return result


def _load_inline_thread_map(jobs: list[GitHubPublishJobORM]) -> dict[str, int]:
    merged: dict[str, int] = {}
    for prior in jobs:
        summary = prior.summary_json
        if not isinstance(summary, dict):
            continue
        inline = summary.get("github_inline_threads")
        merged.update(deserialize_inline_thread_map(inline))
    return merged


def _load_v2_inline_thread_map(jobs: list[GitHubPublishJobORM]) -> dict[str, dict[str, int | str]]:
    merged: dict[str, dict[str, int | str]] = {}
    for prior in jobs:
        summary = prior.summary_json
        if not isinstance(summary, dict):
            continue
        inline = summary.get("github_inline_threads")
        if not isinstance(inline, dict):
            continue
        for fingerprint, value in inline.items():
            if not isinstance(fingerprint, str):
                continue
            if isinstance(value, int):
                merged[fingerprint] = {"comment_id": value}
            elif isinstance(value, dict):
                comment_id = value.get("comment_id")
                if isinstance(comment_id, int):
                    entry: dict[str, int | str] = {"comment_id": comment_id}
                    thread_id = value.get("thread_id")
                    if isinstance(thread_id, str) and thread_id:
                        entry["thread_id"] = thread_id
                    merged[fingerprint] = entry
    return merged


def _fingerprint_thread_ids_from_index(
    comment_map: dict[str, int],
    thread_index: dict[int, str],
) -> dict[str, str]:
    thread_ids: dict[str, str] = {}
    for fingerprint, comment_id in comment_map.items():
        thread_id = thread_index.get(comment_id)
        if isinstance(thread_id, str) and thread_id:
            thread_ids[fingerprint] = thread_id
    return thread_ids


async def _fetch_prior_completed_publish_jobs(
    session: AsyncSession,
    *,
    pull_request_id: UUID,
) -> list[GitHubPublishJobORM]:
    revision_ids = list(
        await session.scalars(
            select(GitHubPullRequestRevisionORM.id).where(
                GitHubPullRequestRevisionORM.pull_request_id == pull_request_id,
            )
        )
    )
    if not revision_ids:
        return []
    return list(
        await session.scalars(
            select(GitHubPublishJobORM)
            .where(
                GitHubPublishJobORM.revision_id.in_(revision_ids),
                GitHubPublishJobORM.status == GitHubPublishJobStatus.completed,
            )
            .order_by(GitHubPublishJobORM.created_at.asc())
        )
    )


async def _load_prior_inline_thread_map(
    session: AsyncSession,
    *,
    pull_request_id: UUID,
) -> dict[str, int]:
    jobs = await _fetch_prior_completed_publish_jobs(session, pull_request_id=pull_request_id)
    return _load_inline_thread_map(jobs)


async def _publishable_fingerprints_for_run(
    session: AsyncSession,
    *,
    review_run_id: UUID,
) -> set[str]:
    """Fingerprints of groups with publishable inline findings for this review run."""
    rows = await session.scalars(
        select(GitHubFindingGroupORM.fingerprint)
        .join(GitHubFindingORM, GitHubFindingORM.group_id == GitHubFindingGroupORM.id)
        .where(
            GitHubFindingORM.review_run_id == review_run_id,
            GitHubFindingGroupORM.state == GitHubFindingGroupState.active,
            GitHubFindingORM.severity.in_(
                (
                    FindingSeverity.error,
                    FindingSeverity.critical,
                    FindingSeverity.warning,
                    FindingSeverity.info,
                ),
            ),
            GitHubFindingORM.file_path.is_not(None),
            GitHubFindingORM.start_line.is_not(None),
        )
        .distinct()
    )
    return set(rows)


async def _resolve_stale_inline_threads(
    client: httpx.AsyncClient,
    *,
    session: AsyncSession,
    review_run_id: UUID,
    github_installation_id: int,
    owner: str,
    repo_name: str,
    pull_request_id: UUID,
    pull_number: int,
    inline_threads: dict[str, int],
    auth_headers: dict[str, str],
    thread_index: dict[int, str] | None = None,
) -> None:
    if not inline_threads:
        return

    publishable = await _publishable_fingerprints_for_run(session, review_run_id=review_run_id)
    fingerprints_to_resolve: set[str] = {
        fingerprint for fingerprint in inline_threads if fingerprint not in publishable
    }

    closed_groups = list(
        await session.scalars(
            select(GitHubFindingGroupORM).where(
                GitHubFindingGroupORM.pull_request_id == pull_request_id,
                GitHubFindingGroupORM.state.in_(
                    (
                        GitHubFindingGroupState.superseded,
                        GitHubFindingGroupState.resolved,
                    )
                ),
            )
        )
    )
    for group in closed_groups:
        if group.fingerprint in inline_threads:
            fingerprints_to_resolve.add(group.fingerprint)

    for fingerprint in fingerprints_to_resolve:
        comment_id = inline_threads.get(fingerprint)
        if comment_id is None:
            continue
        try:
            if thread_index is not None:
                thread_id = thread_index.get(comment_id)
            else:
                thread_id = await github_api.find_review_thread_id_for_comment(
                    client,
                    github_installation_id=github_installation_id,
                    owner=owner,
                    repo=repo_name,
                    pull_number=pull_number,
                    comment_database_id=comment_id,
                    auth_headers=auth_headers,
                    thread_index=thread_index,
                )
            if thread_id is None:
                continue
            await github_api.resolve_review_thread(
                client,
                github_installation_id=github_installation_id,
                thread_id=thread_id,
                auth_headers=auth_headers,
            )
            inline_threads.pop(fingerprint, None)
        except (httpx.HTTPError, ServiceUnavailableError) as exc:
            logger.warning(
                "github_publish_resolve_inline_thread_skipped",
                extra={
                    "pull_request_id": str(pull_request_id),
                    "fingerprint": fingerprint,
                    "comment_id": comment_id,
                    "error": str(exc),
                },
            )


async def find_publish_job_for_head_sha(
    session: AsyncSession,
    *,
    pull_request_id: UUID,
    head_sha: str,
) -> GitHubPublishJobORM | None:
    revision_ids = list(
        await session.scalars(
            select(GitHubPullRequestRevisionORM.id).where(
                GitHubPullRequestRevisionORM.pull_request_id == pull_request_id,
            )
        )
    )
    if not revision_ids:
        return None
    return await session.scalar(
        select(GitHubPublishJobORM)
        .where(
            GitHubPublishJobORM.revision_id.in_(revision_ids),
            GitHubPublishJobORM.head_sha == head_sha,
            GitHubPublishJobORM.github_check_run_id.is_not(None),
            GitHubPublishJobORM.status == GitHubPublishJobStatus.completed,
        )
        .order_by(GitHubPublishJobORM.created_at.desc())
        .limit(1)
    )


async def find_prior_issue_comment_id_for_pull_request(
    session: AsyncSession,
    *,
    pull_request_id: UUID,
    exclude_job_id: UUID | None = None,
) -> int | None:
    """Latest issue comment id on this PR — reuse across pushes (R6-Q1 idempotent surface)."""
    revision_ids = list(
        await session.scalars(
            select(GitHubPullRequestRevisionORM.id).where(
                GitHubPullRequestRevisionORM.pull_request_id == pull_request_id,
            )
        )
    )
    if not revision_ids:
        return None
    stmt = (
        select(GitHubPublishJobORM.github_comment_id)
        .where(
            GitHubPublishJobORM.revision_id.in_(revision_ids),
            GitHubPublishJobORM.github_comment_id.is_not(None),
            GitHubPublishJobORM.status == GitHubPublishJobStatus.completed,
        )
        .order_by(GitHubPublishJobORM.created_at.desc())
        .limit(1)
    )
    if exclude_job_id is not None:
        stmt = stmt.where(GitHubPublishJobORM.id != exclude_job_id)
    comment_id = await session.scalar(stmt)
    return comment_id if isinstance(comment_id, int) else None


async def create_publish_job(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    repository_id: UUID,
    pull_request_id: UUID,
    revision_id: UUID,
    review_run_id: UUID | None = None,
) -> GitHubPublishJobORM:
    if not settings.github_api_enabled:
        raise ServiceUnavailableError(
            message="GitHub App API is not configured",
            error_code="github_api_disabled",
        )

    await ensure_revision_access(
        session,
        workspace_id=workspace_id,
        repository_id=repository_id,
        pull_request_id=pull_request_id,
        revision_id=revision_id,
    )

    if review_run_id is None:
        run = await session.scalar(
            select(GitHubReviewRunORM)
            .where(
                GitHubReviewRunORM.workspace_id == workspace_id,
                GitHubReviewRunORM.revision_id == revision_id,
                GitHubReviewRunORM.status == GitHubReviewRunStatus.completed,
            )
            .order_by(GitHubReviewRunORM.created_at.desc())
            .limit(1)
        )
        if run is None:
            raise ConflictError(
                message="Completed review run required before publish",
                error_code="review_required",
            )
        review_run_id = run.id
    else:
        run = await session.get(GitHubReviewRunORM, review_run_id)
        if run is None or run.status != GitHubReviewRunStatus.completed:
            raise ConflictError(
                message="Completed review run required before publish",
                error_code="review_required",
            )

    revision = await session.get(GitHubPullRequestRevisionORM, revision_id)
    if revision is None:
        raise NotFoundError("Pull request revision not found")

    in_progress = await session.scalar(
        select(GitHubPublishJobORM.id)
        .where(
            GitHubPublishJobORM.review_run_id == review_run_id,
            GitHubPublishJobORM.status.in_(
                (GitHubPublishJobStatus.pending, GitHubPublishJobStatus.processing),
            ),
        )
        .limit(1)
    )
    if in_progress is not None:
        existing_job = await session.get(GitHubPublishJobORM, in_progress)
        if existing_job is not None:
            return existing_job
        raise ConflictError(
            message="Publish is already in progress for this review run",
            error_code="publish_in_progress",
        )

    job = GitHubPublishJobORM(
        review_run_id=review_run_id,
        revision_id=revision_id,
        workspace_id=workspace_id,
        head_sha=revision.head_sha,
        status=GitHubPublishJobStatus.pending,
    )
    session.add(job)
    await session.flush()
    return job


def enqueue_publish_job(publish_job_id: UUID) -> None:
    from app.workers.publish_tasks import dispatch_publish_review_run

    dispatch_publish_review_run(str(publish_job_id))


def enqueue_publish_for_review_run(review_run_id: UUID) -> None:
    if not settings.github_api_enabled:
        logger.info(
            "github_publish_skipped",
            extra={"review_run_id": str(review_run_id), "reason": "github_api_disabled"},
        )
        return
    from app.workers.publish_tasks import publish_for_review_run

    publish_for_review_run.delay(str(review_run_id))


async def _checkpoint_publish_surface(
    session: AsyncSession,
    *,
    persist: bool,
) -> None:
    await session.flush()
    if persist:
        await session.commit()


async def run_publish_job(
    session: AsyncSession,
    *,
    publish_job_id: UUID,
    persist_github_surface: bool = False,
) -> GitHubPublishJobORM:
    started = time.monotonic()
    job = await session.get(GitHubPublishJobORM, publish_job_id)
    if job is None:
        raise NotFoundError("Publish job not found")
    if job.status in _TERMINAL_PUBLISH_JOB_STATUSES:
        return job

    run = await session.get(GitHubReviewRunORM, job.review_run_id)
    revision = await session.get(GitHubPullRequestRevisionORM, job.revision_id)
    if run is None or revision is None:
        job.status = GitHubPublishJobStatus.failed
        job.error_message = "review_run_or_revision_not_found"
        await session.flush()
        return job

    pull_request = await session.get(GitHubPullRequestORM, revision.pull_request_id)
    if pull_request is None:
        job.status = GitHubPublishJobStatus.failed
        job.error_message = "pull_request_context_not_found"
        await session.flush()
        return job

    if is_review_run_superseded(run):
        return await _skip_publish_job_at_gate(
            session,
            job,
            skip_status=GitHubPublishJobStatus.skipped_superseded,
            log_event="publish_skipped_superseded",
        )
    if job.head_sha != pull_request.head_sha:
        return await _skip_publish_job_at_gate(
            session,
            job,
            skip_status=GitHubPublishJobStatus.skipped_not_head,
            log_event="publish_skipped_not_head",
        )

    repository = await session.get(GitHubRepositoryORM, pull_request.repository_id)
    installation = await session.get(GitHubInstallationORM, pull_request.installation_id)
    if repository is None or installation is None:
        job.status = GitHubPublishJobStatus.failed
        job.error_message = "pull_request_context_not_found"
        await session.flush()
        return job

    job.status = GitHubPublishJobStatus.processing
    job.error_message = None
    await session.flush()

    groups = list(
        await session.scalars(
            select(GitHubFindingGroupORM)
            .where(
                GitHubFindingGroupORM.pull_request_id == pull_request.id,
                GitHubFindingGroupORM.state != GitHubFindingGroupState.superseded,
            )
            .order_by(
                _PUBLISH_GROUP_SEVERITY_ORDER,
                GitHubFindingGroupORM.file_path.asc().nulls_last(),
                GitHubFindingGroupORM.title,
                GitHubFindingGroupORM.id,
            )
        )
    )

    conclusion = compute_check_conclusion(groups)
    index_job = await get_latest_completed_index_job(
        session,
        workspace_id=job.workspace_id,
        revision_id=job.revision_id,
    )
    formatted = await build_publish_format_result_async(
        PublishFormatContext(
            pull_request_id=pull_request.id,
            pull_request_number=pull_request.number,
            head_sha=job.head_sha,
            revision_number=revision.revision_number,
            groups=groups,
            index_mode=index_job.index_mode if index_job is not None else None,
            fallback_reason=index_job.fallback_reason if index_job is not None else None,
        )
    )
    check_summary = formatted.check_summary
    issue_comment = formatted.issue_comment
    prior_jobs = await _fetch_prior_completed_publish_jobs(
        session,
        pull_request_id=pull_request.id,
    )
    inline_threads = _load_inline_thread_map(prior_jobs)
    prior_v2 = _load_v2_inline_thread_map(prior_jobs)
    job.summary_json = {
        **formatted.summary_json,
        "github_inline_threads": serialize_inline_thread_map(
            inline_threads,
            prior_v2=prior_v2,
        ),
    }
    owner, repo_name = repository.full_name.split("/", 1)
    external_id = github_api.build_check_run_external_id(
        github_installation_id=installation.github_installation_id,
        github_pr_number=pull_request.number,
        head_sha=job.head_sha,
    )

    existing = await find_publish_job_for_head_sha(
        session,
        pull_request_id=pull_request.id,
        head_sha=job.head_sha,
    )
    is_update_from_other = (
        job.github_check_run_id is None
        and existing is not None
        and existing.id != job.id
        and existing.github_check_run_id is not None
    )
    post_inline = not job.inline_comments_posted and (
        not is_update_from_other
        or existing is None
        or not existing.inline_comments_posted
    )

    if job.github_comment_id is None:
        prior_comment_id = await find_prior_issue_comment_id_for_pull_request(
            session,
            pull_request_id=pull_request.id,
            exclude_job_id=job.id,
        )
        if prior_comment_id is not None:
            job.github_comment_id = prior_comment_id

    try:
        async with httpx.AsyncClient(timeout=120.0) as client:
            auth_headers = await github_api.installation_auth_headers(
                client,
                github_installation_id=installation.github_installation_id,
            )
            if job.github_check_run_id is not None:
                await github_api.update_check_run(
                    client,
                    github_installation_id=installation.github_installation_id,
                    owner=owner,
                    repo=repo_name,
                    check_run_id=job.github_check_run_id,
                    conclusion=conclusion,
                    summary=check_summary,
                    auth_headers=auth_headers,
                )
                if job.github_comment_id is not None:
                    await github_api.update_issue_comment(
                        client,
                        github_installation_id=installation.github_installation_id,
                        owner=owner,
                        repo=repo_name,
                        comment_id=job.github_comment_id,
                        body=issue_comment,
                        auth_headers=auth_headers,
                    )
                else:
                    comment_id = await github_api.create_issue_comment(
                        client,
                        github_installation_id=installation.github_installation_id,
                        owner=owner,
                        repo=repo_name,
                        issue_number=pull_request.number,
                        body=issue_comment,
                        auth_headers=auth_headers,
                    )
                    job.github_comment_id = comment_id
                    await _checkpoint_publish_surface(session, persist=persist_github_surface)
            elif is_update_from_other and existing is not None:
                job.github_check_run_id = existing.github_check_run_id
                await github_api.update_check_run(
                    client,
                    github_installation_id=installation.github_installation_id,
                    owner=owner,
                    repo=repo_name,
                    check_run_id=existing.github_check_run_id,
                    conclusion=conclusion,
                    summary=check_summary,
                    auth_headers=auth_headers,
                )
                if existing.github_comment_id is not None:
                    job.github_comment_id = existing.github_comment_id
                    await github_api.update_issue_comment(
                        client,
                        github_installation_id=installation.github_installation_id,
                        owner=owner,
                        repo=repo_name,
                        comment_id=existing.github_comment_id,
                        body=issue_comment,
                        auth_headers=auth_headers,
                    )
                else:
                    comment_id = await github_api.create_issue_comment(
                        client,
                        github_installation_id=installation.github_installation_id,
                        owner=owner,
                        repo=repo_name,
                        issue_number=pull_request.number,
                        body=issue_comment,
                        auth_headers=auth_headers,
                    )
                    job.github_comment_id = comment_id
                    await _checkpoint_publish_surface(session, persist=persist_github_surface)
            else:
                check_run_id = await github_api.create_check_run(
                    client,
                    github_installation_id=installation.github_installation_id,
                    owner=owner,
                    repo=repo_name,
                    head_sha=job.head_sha,
                    external_id=external_id,
                    conclusion=conclusion,
                    summary=check_summary,
                    auth_headers=auth_headers,
                )
                job.github_check_run_id = check_run_id
                await _checkpoint_publish_surface(session, persist=persist_github_surface)

                comment_id = await github_api.create_issue_comment(
                    client,
                    github_installation_id=installation.github_installation_id,
                    owner=owner,
                    repo=repo_name,
                    issue_number=pull_request.number,
                    body=issue_comment,
                    auth_headers=auth_headers,
                )
                job.github_comment_id = comment_id
                await _checkpoint_publish_surface(session, persist=persist_github_surface)

            thread_index: dict[int, str] = {}
            if inline_threads:
                thread_index = await github_api.build_review_thread_comment_index(
                    client,
                    github_installation_id=installation.github_installation_id,
                    owner=owner,
                    repo=repo_name,
                    pull_number=pull_request.number,
                    auth_headers=auth_headers,
                )

            await _resolve_stale_inline_threads(
                client,
                session=session,
                review_run_id=job.review_run_id,
                github_installation_id=installation.github_installation_id,
                owner=owner,
                repo_name=repo_name,
                pull_request_id=pull_request.id,
                pull_number=pull_request.number,
                inline_threads=inline_threads,
                auth_headers=auth_headers,
                thread_index=thread_index,
            )

            prior_v2 = (job.summary_json or {}).get("github_inline_threads")
            indexed_thread_ids = _fingerprint_thread_ids_from_index(inline_threads, thread_index)
            job.summary_json = {
                **(job.summary_json or {}),
                "github_inline_threads": serialize_inline_thread_map(
                    inline_threads,
                    prior_v2=prior_v2 if isinstance(prior_v2, dict) else None,
                    thread_ids=indexed_thread_ids,
                ),
            }

            if post_inline:
                inline_findings = list(
                    await session.scalars(
                        inline_publish_findings_statement(review_run_id=job.review_run_id).order_by(
                            GitHubFindingORM.file_path,
                            GitHubFindingORM.start_line,
                            GitHubFindingORM.id,
                        )
                    )
                )
                inline_thread_ids: dict[str, str] = {}
                for finding in inline_findings:
                    if finding.file_path is None or finding.start_line is None:
                        continue
                    group = (
                        await session.get(GitHubFindingGroupORM, finding.group_id)
                        if finding.group_id is not None
                        else None
                    )
                    if group is None:
                        logger.warning(
                            "github_publish_inline_skipped_no_group",
                            extra={
                                "publish_job_id": str(publish_job_id),
                                "finding_id": str(finding.id),
                            },
                        )
                        continue
                    try:
                        comment_id = await github_api.create_pull_request_review_comment(
                            client,
                            github_installation_id=installation.github_installation_id,
                            owner=owner,
                            repo=repo_name,
                            pull_number=pull_request.number,
                            commit_id=job.head_sha,
                            path=finding.file_path,
                            line=finding.start_line,
                            body=github_api.format_inline_comment_body(
                                title=finding.title,
                                message=finding.message,
                                severity=stored_enum_value(finding.severity),
                                suggestion=is_publishable_suggestion(finding),
                            ),
                            auth_headers=auth_headers,
                        )
                        inline_threads[group.fingerprint] = comment_id
                        thread_id = thread_index.get(comment_id)
                        if isinstance(thread_id, str) and thread_id:
                            inline_thread_ids[group.fingerprint] = thread_id
                    except httpx.HTTPStatusError as exc:
                        if exc.response.status_code in (404, 422):
                            logger.warning(
                                "github_publish_inline_comment_skipped",
                                extra={
                                    "publish_job_id": str(publish_job_id),
                                    "file_path": finding.file_path,
                                    "line": finding.start_line,
                                    "status_code": exc.response.status_code,
                                },
                            )
                            continue
                        raise
                prior_v2 = (job.summary_json or {}).get("github_inline_threads")
                job.summary_json = {
                    **(job.summary_json or {}),
                    "github_inline_threads": serialize_inline_thread_map(
                        inline_threads,
                        prior_v2=prior_v2 if isinstance(prior_v2, dict) else None,
                        thread_ids=inline_thread_ids,
                    ),
                }
                job.inline_comments_posted = True
                await _checkpoint_publish_surface(session, persist=persist_github_surface)
            elif persist_github_surface:
                await _checkpoint_publish_surface(session, persist=persist_github_surface)

        job.status = GitHubPublishJobStatus.completed
        await session.flush()
        pipeline_run = await get_pipeline_run_for_review_run(session, review_run_id=job.review_run_id)
        if pipeline_run is not None:
            await record_publish_pipeline_step(
                session,
                pipeline_run_id=pipeline_run.id,
                job=job,
                summary_markdown=check_summary,
                issue_comment_markdown=issue_comment,
                duration_ms=int((time.monotonic() - started) * 1000),
            )
        return job
    except (httpx.HTTPError, ServiceUnavailableError) as exc:
        retryable = classify_transient_error(exc)
        if retryable is not None:
            logger.warning(
                "github_publish_job_transient_failure",
                extra={"publish_job_id": str(publish_job_id), "error": str(exc)},
            )
            raise PublishJobRetryableError(str(exc)) from exc
        logger.error(
            "github_publish_job_failed",
            extra={"publish_job_id": str(publish_job_id), "error": str(exc)},
        )
        job.status = GitHubPublishJobStatus.failed
        job.error_message = str(exc)[:2000]
        await session.flush()
        pipeline_run = await get_pipeline_run_for_review_run(session, review_run_id=job.review_run_id)
        if pipeline_run is not None:
            await record_publish_pipeline_step(
                session,
                pipeline_run_id=pipeline_run.id,
                job=job,
                summary_markdown=job.error_message or "Publish failed",
                duration_ms=int((time.monotonic() - started) * 1000),
            )
            await finalize_pipeline_github_check_failure(
                session,
                pipeline_run_id=pipeline_run.id,
                summary=job.error_message,
            )
        return job
