# backend/app/services/github_publish.py
"""GitHub publish pipeline — R6."""

from __future__ import annotations

import time
from dataclasses import dataclass
from uuid import UUID

import httpx
from sqlalchemy import and_, case, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import (
    FindingSeverity,
    GitHubFindingGroupState,
    GitHubPublishJobStatus,
    GitHubReviewRunStatus,
    ResolutionStatus,
    stored_enum_value,
)
from app.core.config import settings
from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    RateLimitedError,
    ServiceUnavailableError,
)
from app.core.logging import get_logger
from app.core.worker_retries import (
    WorkerRetryableError,
    classify_transient_error,
    is_retryable_http_status,
)
from app.integrations import github_api
from app.models.github_finding import GitHubFindingORM
from app.models.github_finding_group import GitHubFindingGroupORM
from app.models.github_finding_judge_outcome import GitHubFindingJudgeOutcomeORM
from app.models.github_installation import GitHubInstallationORM
from app.models.github_publish_job import GitHubPublishJobORM
from app.models.github_pull_request import (
    GitHubPullRequestORM,
    GitHubPullRequestRevisionORM,
)
from app.models.github_repository import GitHubRepositoryORM
from app.models.github_review_run import GitHubReviewRunORM
from app.services.github_finding_judge import is_judge_candidate
from app.services.github_generation_lifecycle import is_review_run_superseded
from app.services.github_indexing import ensure_revision_access, get_latest_completed_index_job
from app.services.github_pipeline_trace import (
    finalize_pipeline_github_check_failure,
    finalize_pipeline_github_check_neutral,
    get_pipeline_run_for_review_run,
    get_resolution_metrics_for_review_run,
    link_publish_job_to_pipeline,
    record_publish_pipeline_step,
    record_publish_skip_on_pipeline,
    resolve_pipeline_github_check_run_id,
)
from app.services.github_publish_formatter import (
    PublishFormatContext,
    append_thread_resolve_skipped_block,
    build_publish_format_result_async,
)
from app.services.github_suggestion import is_publishable_suggestion

logger = get_logger(__name__)

THREAD_RESOLVE_SKIP_ALREADY_RESOLVED = "already_resolved"
THREAD_RESOLVE_SKIP_THREAD_ID_NOT_FOUND = "thread_id_not_found"
THREAD_RESOLVE_SKIP_RESOLVE_MUTATION_FAILED = "resolve_mutation_failed"
THREAD_RESOLVE_SKIP_THREAD_NOT_REVY_OWNED = "thread_not_revy_owned"

_THREAD_RESOLVE_SKIP_REASONS = (
    THREAD_RESOLVE_SKIP_ALREADY_RESOLVED,
    THREAD_RESOLVE_SKIP_THREAD_ID_NOT_FOUND,
    THREAD_RESOLVE_SKIP_RESOLVE_MUTATION_FAILED,
    THREAD_RESOLVE_SKIP_THREAD_NOT_REVY_OWNED,
)


def empty_thread_resolve_skipped() -> dict[str, int]:
    return {reason: 0 for reason in _THREAD_RESOLVE_SKIP_REASONS}


def increment_thread_resolve_skip(skipped: dict[str, int], reason: str) -> None:
    if reason not in skipped:
        skipped[reason] = 0
    skipped[reason] += 1


def _log_thread_resolve_skipped(
    *,
    pull_request_id: UUID,
    fingerprint: str,
    comment_id: int | None,
    reason: str,
    error: str | None = None,
) -> None:
    extra: dict[str, object] = {
        "pull_request_id": str(pull_request_id),
        "fingerprint": fingerprint,
        "reason": reason,
    }
    if comment_id is not None:
        extra["comment_id"] = comment_id
    if error is not None:
        extra["error"] = error[:500]
    logger.warning("github_publish_resolve_inline_thread_skipped", extra=extra)


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

_INLINE_422_RECOVERED_COUNT_KEY = "inline_publish_422_recovered_count"
_INLINE_422_RECOVERED_FINGERPRINTS_KEY = "inline_publish_422_recovered_fingerprints"
_INLINE_422_FALLBACK_MARKER_PREFIX = "<!-- revy:inline-422:"

_TERMINAL_PUBLISH_JOB_STATUSES = frozenset(
    {
        GitHubPublishJobStatus.completed,
        GitHubPublishJobStatus.failed,
        GitHubPublishJobStatus.skipped_not_head,
        GitHubPublishJobStatus.skipped_superseded,
    }
)

_PUBLISH_SURFACE_REUSE_STATUSES = (
    GitHubPublishJobStatus.completed,
    GitHubPublishJobStatus.skipped_not_head,
    GitHubPublishJobStatus.skipped_superseded,
)

_PUBLISH_INLINE_THREAD_REUSE_STATUSES = (GitHubPublishJobStatus.completed,)


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
    skip_manifest_key = {
        GitHubPublishJobStatus.skipped_not_head: "publish_skipped_not_head",
        GitHubPublishJobStatus.skipped_superseded: "publish_skipped_superseded",
    }.get(skip_status)
    if skip_manifest_key is not None:
        await record_publish_skip_on_pipeline(
            session,
            review_run_id=job.review_run_id,
            manifest_key=skip_manifest_key,
        )
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


async def _recheck_publish_authority_before_flush(
    session: AsyncSession,
    job: GitHubPublishJobORM,
    run: GitHubReviewRunORM,
    pull_request: GitHubPullRequestORM,
) -> GitHubPublishJobORM | None:
    """Re-read authority after build — HEAD may advance during slow format/build."""
    await session.refresh(run)
    await session.refresh(pull_request)
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
    return None


async def _neutralize_github_check_after_partial_flush(
    client: httpx.AsyncClient,
    *,
    github_installation_id: int,
    owner: str,
    repo_name: str,
    job: GitHubPublishJobORM,
    auth_headers: dict[str, str],
) -> None:
    check_run_id = job.github_check_run_id
    if check_run_id is None:
        return
    await github_api.update_check_run(
        client,
        github_installation_id=github_installation_id,
        owner=owner,
        repo=repo_name,
        check_run_id=check_run_id,
        conclusion="neutral",
        summary=_SKIP_PUBLISH_NEUTRAL_SUMMARY,
        auth_headers=auth_headers,
    )


async def _neutralize_github_issue_comment_after_partial_flush(
    client: httpx.AsyncClient,
    *,
    github_installation_id: int,
    owner: str,
    repo_name: str,
    job: GitHubPublishJobORM,
    auth_headers: dict[str, str],
) -> None:
    comment_id = job.github_comment_id
    if comment_id is None:
        return
    await github_api.update_issue_comment(
        client,
        github_installation_id=github_installation_id,
        owner=owner,
        repo=repo_name,
        comment_id=comment_id,
        body=_SKIP_PUBLISH_NEUTRAL_SUMMARY,
        auth_headers=auth_headers,
    )


async def _best_effort_revert_partial_flush_surface(
    client: httpx.AsyncClient,
    *,
    github_installation_id: int,
    owner: str,
    repo_name: str,
    job: GitHubPublishJobORM,
    auth_headers: dict[str, str],
    github_check_written: bool,
    github_comment_written: bool,
    publish_job_id: UUID,
    inline_comment_ids: list[int] | None = None,
) -> None:
    if github_check_written:
        try:
            await _neutralize_github_check_after_partial_flush(
                client,
                github_installation_id=github_installation_id,
                owner=owner,
                repo_name=repo_name,
                job=job,
                auth_headers=auth_headers,
            )
        except (httpx.HTTPError, ServiceUnavailableError) as exc:
            logger.warning(
                "publish_partial_flush_check_neutralize_failed",
                extra={"publish_job_id": str(publish_job_id), "error": str(exc)},
            )
    if github_comment_written:
        try:
            await _neutralize_github_issue_comment_after_partial_flush(
                client,
                github_installation_id=github_installation_id,
                owner=owner,
                repo_name=repo_name,
                job=job,
                auth_headers=auth_headers,
            )
        except (httpx.HTTPError, ServiceUnavailableError) as exc:
            logger.warning(
                "publish_partial_flush_comment_neutralize_failed",
                extra={"publish_job_id": str(publish_job_id), "error": str(exc)},
            )
    for comment_id in inline_comment_ids or []:
        try:
            await github_api.delete_pull_request_review_comment(
                client,
                github_installation_id=github_installation_id,
                owner=owner,
                repo=repo_name,
                comment_id=comment_id,
                auth_headers=auth_headers,
            )
        except (httpx.HTTPError, ServiceUnavailableError) as exc:
            logger.warning(
                "publish_partial_flush_inline_delete_failed",
                extra={
                    "publish_job_id": str(publish_job_id),
                    "comment_id": comment_id,
                    "error": str(exc),
                },
            )


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
        select(GitHubReviewRunORM).where(GitHubReviewRunORM.id == review_run_id).with_for_update()
    )
    if run is None or run.status != GitHubReviewRunStatus.completed:
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
                if prior_comment_id == comment_id and isinstance(thread_id, str) and thread_id:
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
                GitHubPublishJobORM.status.in_(_PUBLISH_INLINE_THREAD_REUSE_STATUSES),
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
    pull_request_id: UUID,
) -> set[str]:
    """Fingerprints eligible for inline publish (aligned with build inline_posts judge gate)."""
    outcome_group_ids = set(
        await session.scalars(
            select(GitHubFindingJudgeOutcomeORM.group_id).where(
                GitHubFindingJudgeOutcomeORM.review_run_id == review_run_id,
            )
        )
    )
    fingerprints: set[str] = set()
    inline_findings = list(
        await session.scalars(inline_publish_findings_statement(review_run_id=review_run_id))
    )
    for finding in inline_findings:
        if finding.group_id is None:
            continue
        group = await session.get(GitHubFindingGroupORM, finding.group_id)
        if group is None or group.pull_request_id != pull_request_id:
            continue
        if (
            is_judge_candidate(severity=finding.severity, category=finding.category)
            and group.id not in outcome_group_ids
            and group.state != GitHubFindingGroupState.resolved
        ):
            continue
        fingerprints.add(group.fingerprint)
    return fingerprints


async def _fingerprints_to_resolve_inline_threads(
    session: AsyncSession,
    *,
    review_run_id: UUID,
    pull_request_id: UUID,
    inline_threads: dict[str, int],
    outdated_comment_ids: frozenset[int] | None = None,
) -> set[str]:
    publishable = await _publishable_fingerprints_for_run(
        session,
        review_run_id=review_run_id,
        pull_request_id=pull_request_id,
    )
    fingerprints_to_resolve: set[str] = {
        fingerprint for fingerprint in inline_threads if fingerprint not in publishable
    }
    if outdated_comment_ids:
        for fingerprint, comment_id in inline_threads.items():
            if comment_id in outdated_comment_ids:
                fingerprints_to_resolve.add(fingerprint)

    tracked_fingerprints = tuple(inline_threads.keys())
    if tracked_fingerprints:
        groups = list(
            await session.scalars(
                select(GitHubFindingGroupORM).where(
                    GitHubFindingGroupORM.pull_request_id == pull_request_id,
                    or_(
                        GitHubFindingGroupORM.state.in_(
                            (
                                GitHubFindingGroupState.superseded,
                                GitHubFindingGroupState.resolved,
                            )
                        ),
                        and_(
                            GitHubFindingGroupORM.fingerprint.in_(tracked_fingerprints),
                            GitHubFindingGroupORM.resolution_status == ResolutionStatus.addressed,
                        ),
                    ),
                )
            )
        )
        # v2 (post GH-Q2): collapse when Pass 1 stamped addressed even if Moonshot
        # re-reports the same fingerprint — avoids stale open threads on fix pushes.
        for group in groups:
            if group.fingerprint in inline_threads:
                fingerprints_to_resolve.add(group.fingerprint)
    return fingerprints_to_resolve


def inline_422_fallback_marker(fingerprint: str) -> str:
    return f"{_INLINE_422_FALLBACK_MARKER_PREFIX}{fingerprint} -->"


def _is_transient_thread_resolve_error(exc: BaseException) -> bool:
    if isinstance(exc, ServiceUnavailableError):
        return True
    if isinstance(exc, RateLimitedError):
        return False
    if isinstance(exc, httpx.HTTPStatusError):
        status_code = exc.response.status_code
        return is_retryable_http_status(status_code) and status_code != 429
    return isinstance(exc, httpx.TransportError)


def _inline_422_fallback_blocks_for_specs(
    inline_posts: list[InlinePostSpec],
    recovered_fingerprints: set[str],
) -> list[str]:
    return [
        _format_inline_422_fallback_block(spec)
        for spec in inline_posts
        if spec.group_fingerprint in recovered_fingerprints
    ]


def _append_missing_inline_422_fallback_blocks(
    issue_comment_body: str,
    fallback_blocks: list[str],
) -> str | None:
    missing = [
        block
        for block in fallback_blocks
        if block
        and all(
            marker not in issue_comment_body
            for marker in (
                line
                for line in block.splitlines()
                if line.startswith(_INLINE_422_FALLBACK_MARKER_PREFIX)
            )
        )
    ]
    if not missing:
        return None
    return f"{issue_comment_body.rstrip()}\n\n" + "\n\n".join(missing)


def _issue_comment_id_for_publish_flush(
    job: GitHubPublishJobORM,
    build: PublishSurfaceBuild,
) -> int | None:
    if job.github_comment_id is not None:
        return job.github_comment_id
    return build.existing_github_comment_id


async def _append_recovered_inline_422_blocks_to_issue_comment(
    client: httpx.AsyncClient,
    *,
    github_installation_id: int,
    owner: str,
    repo_name: str,
    job: GitHubPublishJobORM,
    build: PublishSurfaceBuild,
    issue_comment_body: str,
    recovered_fingerprints: set[str],
    auth_headers: dict[str, str],
) -> str:
    comment_id = _issue_comment_id_for_publish_flush(job, build)
    if comment_id is None:
        return issue_comment_body

    updated_body = _append_missing_inline_422_fallback_blocks(
        issue_comment_body,
        _inline_422_fallback_blocks_for_specs(build.inline_posts, recovered_fingerprints),
    )
    if updated_body is None:
        return issue_comment_body

    await github_api.update_issue_comment(
        client,
        github_installation_id=github_installation_id,
        owner=owner,
        repo=repo_name,
        comment_id=comment_id,
        body=updated_body,
        auth_headers=auth_headers,
    )
    if job.github_comment_id is None:
        job.github_comment_id = comment_id
    return updated_body


async def _resolve_review_thread_with_retry(
    client: httpx.AsyncClient,
    *,
    github_installation_id: int,
    thread_id: str,
    auth_headers: dict[str, str],
) -> None:
    try:
        await github_api.resolve_review_thread(
            client,
            github_installation_id=github_installation_id,
            thread_id=thread_id,
            auth_headers=auth_headers,
        )
    except Exception as exc:
        if not _is_transient_thread_resolve_error(exc):
            raise
        await github_api.resolve_review_thread(
            client,
            github_installation_id=github_installation_id,
            thread_id=thread_id,
            auth_headers=auth_headers,
        )


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
    outdated_comment_ids: frozenset[int] | None = None,
    resolved_comment_ids: frozenset[int] | None = None,
) -> dict[str, int]:
    skipped = empty_thread_resolve_skipped()
    if not inline_threads:
        return skipped

    fingerprints_to_resolve = await _fingerprints_to_resolve_inline_threads(
        session,
        review_run_id=review_run_id,
        pull_request_id=pull_request_id,
        inline_threads=inline_threads,
        outdated_comment_ids=outdated_comment_ids,
    )

    for fingerprint in fingerprints_to_resolve:
        comment_id = inline_threads.get(fingerprint)
        if comment_id is None:
            continue
        if resolved_comment_ids and comment_id in resolved_comment_ids:
            increment_thread_resolve_skip(skipped, THREAD_RESOLVE_SKIP_ALREADY_RESOLVED)
            inline_threads.pop(fingerprint, None)
            continue
        try:
            thread_id = thread_index.get(comment_id) if thread_index else None
            if thread_id is None:
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
                _log_thread_resolve_skipped(
                    pull_request_id=pull_request_id,
                    fingerprint=fingerprint,
                    comment_id=comment_id,
                    reason=THREAD_RESOLVE_SKIP_THREAD_ID_NOT_FOUND,
                )
                increment_thread_resolve_skip(skipped, THREAD_RESOLVE_SKIP_THREAD_ID_NOT_FOUND)
                continue
            await _resolve_review_thread_with_retry(
                client,
                github_installation_id=github_installation_id,
                thread_id=thread_id,
                auth_headers=auth_headers,
            )
            inline_threads.pop(fingerprint, None)
        except (httpx.HTTPError, RateLimitedError, ServiceUnavailableError) as exc:
            _log_thread_resolve_skipped(
                pull_request_id=pull_request_id,
                fingerprint=fingerprint,
                comment_id=comment_id,
                reason=THREAD_RESOLVE_SKIP_RESOLVE_MUTATION_FAILED,
                error=str(exc),
            )
            increment_thread_resolve_skip(skipped, THREAD_RESOLVE_SKIP_RESOLVE_MUTATION_FAILED)

    return skipped


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
            GitHubPublishJobORM.status.in_(_PUBLISH_SURFACE_REUSE_STATUSES),
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
            GitHubPublishJobORM.status.in_(_PUBLISH_SURFACE_REUSE_STATUSES),
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


@dataclass(frozen=True)
class InlinePostSpec:
    finding_id: UUID
    group_id: UUID
    group_fingerprint: str
    file_path: str
    start_line: int
    title: str
    message: str
    severity: str
    suggestion: str | None


def _nearest_inline_retry_line(start_line: int) -> int:
    return start_line - 1 if start_line > 1 else start_line + 1


def _load_inline_422_recovered_fingerprints(summary_json: dict | None) -> frozenset[str]:
    if not isinstance(summary_json, dict):
        return frozenset()
    raw = summary_json.get(_INLINE_422_RECOVERED_FINGERPRINTS_KEY)
    if not isinstance(raw, list):
        return frozenset()
    return frozenset(fp for fp in raw if isinstance(fp, str) and fp)


def _format_inline_422_fallback_block(spec: InlinePostSpec) -> str:
    body = github_api.format_inline_comment_body(
        title=spec.title,
        message=spec.message,
        severity=spec.severity,
        suggestion=spec.suggestion,
    )
    marker = inline_422_fallback_marker(spec.group_fingerprint)
    return f"{marker}\n### Inline fallback ({spec.file_path}:{spec.start_line})\n\n{body}"


async def _create_inline_review_comment_with_422_retry(
    client: httpx.AsyncClient,
    *,
    github_installation_id: int,
    owner: str,
    repo_name: str,
    pull_number: int,
    commit_id: str,
    spec: InlinePostSpec,
    auth_headers: dict[str, str],
) -> int | None:
    lines_to_try = (spec.start_line, _nearest_inline_retry_line(spec.start_line))
    for line in lines_to_try:
        try:
            return await github_api.create_pull_request_review_comment(
                client,
                github_installation_id=github_installation_id,
                owner=owner,
                repo=repo_name,
                pull_number=pull_number,
                commit_id=commit_id,
                path=spec.file_path,
                line=line,
                body=github_api.format_inline_comment_body(
                    title=spec.title,
                    message=spec.message,
                    severity=spec.severity,
                    suggestion=spec.suggestion,
                ),
                auth_headers=auth_headers,
            )
        except httpx.HTTPStatusError as exc:
            if exc.response.status_code in (404, 422):
                continue
            raise
    return None


@dataclass(frozen=True)
class PublishSurfaceBuild:
    check_summary: str
    issue_comment: str
    conclusion: str
    summary_json: dict
    inline_threads: dict[str, int]
    prior_v2_inline: dict[str, dict[str, int | str]]
    inline_posts: list[InlinePostSpec]
    post_inline: bool
    is_update_from_other: bool
    existing_github_check_run_id: int | None
    existing_github_comment_id: int | None
    existing_inline_comments_posted: bool
    external_id: str
    owner: str
    repo_name: str


def _sort_publishable_groups(groups: list[GitHubFindingGroupORM]) -> list[GitHubFindingGroupORM]:
    severity_rank = {
        FindingSeverity.critical: 0,
        FindingSeverity.error: 1,
        FindingSeverity.warning: 2,
    }
    return sorted(
        groups,
        key=lambda g: (
            severity_rank.get(g.severity, 3),
            g.file_path or "",
            g.title,
            str(g.id),
        ),
    )


async def publishable_groups_for_review_run(
    session: AsyncSession,
    *,
    review_run_id: UUID,
    pull_request_id: UUID,
) -> list[GitHubFindingGroupORM]:
    """Active groups for this review run — judge candidates require outcome or resolved."""
    findings = list(
        await session.scalars(
            select(GitHubFindingORM).where(
                GitHubFindingORM.review_run_id == review_run_id,
                GitHubFindingORM.group_id.is_not(None),
            )
        )
    )
    if not findings:
        return []

    outcome_group_ids = set(
        await session.scalars(
            select(GitHubFindingJudgeOutcomeORM.group_id).where(
                GitHubFindingJudgeOutcomeORM.review_run_id == review_run_id,
            )
        )
    )

    publishable: dict[UUID, GitHubFindingGroupORM] = {}
    for finding in findings:
        if finding.group_id is None:
            continue
        group = await session.get(GitHubFindingGroupORM, finding.group_id)
        if group is None or group.pull_request_id != pull_request_id:
            continue
        if group.state == GitHubFindingGroupState.superseded:
            continue
        if group.state == GitHubFindingGroupState.resolved:
            publishable[group.id] = group
            continue
        if not is_judge_candidate(severity=finding.severity, category=finding.category):
            publishable[group.id] = group
            continue
        if group.id in outcome_group_ids:
            publishable[group.id] = group
        else:
            logger.warning(
                "judge_candidate_unpublished_missing_outcome",
                extra={
                    "group_id": str(group.id),
                    "review_run_id": str(review_run_id),
                },
            )

    return _sort_publishable_groups(list(publishable.values()))


async def _load_pr_active_groups(
    session: AsyncSession,
    *,
    pull_request_id: UUID,
) -> list[GitHubFindingGroupORM]:
    return list(
        await session.scalars(
            select(GitHubFindingGroupORM).where(
                GitHubFindingGroupORM.pull_request_id == pull_request_id,
                GitHubFindingGroupORM.state == GitHubFindingGroupState.active,
            )
        )
    )


async def _build_publish_surface(
    session: AsyncSession,
    *,
    job: GitHubPublishJobORM,
    revision: GitHubPullRequestRevisionORM,
    pull_request: GitHubPullRequestORM,
    repository: GitHubRepositoryORM,
    installation: GitHubInstallationORM,
) -> PublishSurfaceBuild:
    groups = await publishable_groups_for_review_run(
        session,
        review_run_id=job.review_run_id,
        pull_request_id=pull_request.id,
    )
    pr_active_groups = await _load_pr_active_groups(
        session,
        pull_request_id=pull_request.id,
    )
    conclusion = compute_check_conclusion(groups)
    index_job = await get_latest_completed_index_job(
        session,
        workspace_id=job.workspace_id,
        revision_id=job.revision_id,
    )
    resolution_metrics_manifest = await get_resolution_metrics_for_review_run(
        session,
        review_run_id=job.review_run_id,
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
            resolution_metrics_manifest=resolution_metrics_manifest,
            pr_active_groups=pr_active_groups,
        )
    )
    prior_jobs = await _fetch_prior_completed_publish_jobs(
        session,
        pull_request_id=pull_request.id,
    )
    inline_threads = _load_inline_thread_map(prior_jobs)
    prior_v2_inline = _load_v2_inline_thread_map(prior_jobs)
    summary_json = {
        **formatted.summary_json,
        "github_inline_threads": serialize_inline_thread_map(
            inline_threads,
            prior_v2=prior_v2_inline,
        ),
    }

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
        not is_update_from_other or existing is None or not existing.inline_comments_posted
    )

    if job.github_comment_id is None:
        prior_comment_id = await find_prior_issue_comment_id_for_pull_request(
            session,
            pull_request_id=pull_request.id,
            exclude_job_id=job.id,
        )
        if prior_comment_id is not None:
            job.github_comment_id = prior_comment_id

    inline_posts: list[InlinePostSpec] = []
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
                        "publish_job_id": str(job.id),
                        "finding_id": str(finding.id),
                    },
                )
                continue
            if is_judge_candidate(severity=finding.severity, category=finding.category):
                outcome = await session.scalar(
                    select(GitHubFindingJudgeOutcomeORM.id).where(
                        GitHubFindingJudgeOutcomeORM.review_run_id == job.review_run_id,
                        GitHubFindingJudgeOutcomeORM.group_id == group.id,
                    )
                )
                if outcome is None and group.state != GitHubFindingGroupState.resolved:
                    continue
            inline_posts.append(
                InlinePostSpec(
                    finding_id=finding.id,
                    group_id=group.id,
                    group_fingerprint=group.fingerprint,
                    file_path=finding.file_path,
                    start_line=finding.start_line,
                    title=finding.title,
                    message=finding.message,
                    severity=stored_enum_value(finding.severity),
                    suggestion=is_publishable_suggestion(finding),
                )
            )

    owner, repo_name = repository.full_name.split("/", 1)
    external_id = github_api.build_check_run_external_id(
        github_installation_id=installation.github_installation_id,
        github_pr_number=pull_request.number,
        head_sha=job.head_sha,
    )

    return PublishSurfaceBuild(
        check_summary=formatted.check_summary,
        issue_comment=formatted.issue_comment,
        conclusion=conclusion,
        summary_json=summary_json,
        inline_threads=inline_threads,
        prior_v2_inline=prior_v2_inline,
        inline_posts=inline_posts,
        post_inline=post_inline,
        is_update_from_other=is_update_from_other,
        existing_github_check_run_id=existing.github_check_run_id if existing else None,
        existing_github_comment_id=existing.github_comment_id if existing else None,
        existing_inline_comments_posted=existing.inline_comments_posted if existing else False,
        external_id=external_id,
        owner=owner,
        repo_name=repo_name,
    )


async def _flush_publish_surface(
    session: AsyncSession,
    *,
    job: GitHubPublishJobORM,
    publish_job_id: UUID,
    build: PublishSurfaceBuild,
    pull_request: GitHubPullRequestORM,
    installation: GitHubInstallationORM,
    persist_github_surface: bool,
    retry_posted_inline: dict[str, int] | None = None,
    run: GitHubReviewRunORM,
) -> GitHubPublishJobORM | None:
    inline_threads = dict(build.inline_threads)
    retry_posted = retry_posted_inline or {}
    inline_threads.update(retry_posted)

    skipped_at_flush_start = await _recheck_publish_authority_before_flush(
        session,
        job,
        run,
        pull_request,
    )
    if skipped_at_flush_start is not None:
        return skipped_at_flush_start

    async with httpx.AsyncClient(timeout=120.0) as client:
        auth_headers = await github_api.installation_auth_headers(
            client,
            github_installation_id=installation.github_installation_id,
        )

        thread_index: dict[int, str] = {}
        outdated_comment_ids: frozenset[int] = frozenset()
        resolved_comment_ids: frozenset[int] = frozenset()
        if inline_threads:
            review_thread_index = await github_api.build_review_thread_index(
                client,
                github_installation_id=installation.github_installation_id,
                owner=build.owner,
                repo=build.repo_name,
                pull_number=pull_request.number,
                auth_headers=auth_headers,
            )
            thread_index = review_thread_index.comment_to_thread_id
            outdated_comment_ids = review_thread_index.outdated_comment_ids
            resolved_comment_ids = review_thread_index.resolved_comment_ids

        skipped_before_resolve = await _recheck_publish_authority_before_flush(
            session,
            job,
            run,
            pull_request,
        )
        if skipped_before_resolve is not None:
            return skipped_before_resolve

        thread_resolve_skipped = await _resolve_stale_inline_threads(
            client,
            session=session,
            review_run_id=job.review_run_id,
            github_installation_id=installation.github_installation_id,
            owner=build.owner,
            repo_name=build.repo_name,
            pull_request_id=pull_request.id,
            pull_number=pull_request.number,
            inline_threads=inline_threads,
            auth_headers=auth_headers,
            thread_index=thread_index,
            outdated_comment_ids=outdated_comment_ids,
            resolved_comment_ids=resolved_comment_ids,
        )

        issue_comment_body = build.issue_comment
        check_summary_body = build.check_summary
        if any(thread_resolve_skipped.values()):
            issue_comment_body = append_thread_resolve_skipped_block(
                issue_comment_body,
                thread_resolve_skipped,
            )
            check_summary_body = append_thread_resolve_skipped_block(
                check_summary_body,
                thread_resolve_skipped,
            )

        indexed_thread_ids = _fingerprint_thread_ids_from_index(inline_threads, thread_index)
        job.summary_json = {
            **(job.summary_json or {}),
            "github_inline_threads": serialize_inline_thread_map(
                inline_threads,
                prior_v2=build.prior_v2_inline,
                thread_ids=indexed_thread_ids,
            ),
            "thread_resolve_skipped": thread_resolve_skipped,
        }

        skipped_after_resolve = await _recheck_publish_authority_before_flush(
            session,
            job,
            run,
            pull_request,
        )
        if skipped_after_resolve is not None:
            return skipped_after_resolve

        github_check_written = False
        github_comment_written = False
        if job.github_check_run_id is not None:
            await github_api.update_check_run(
                client,
                github_installation_id=installation.github_installation_id,
                owner=build.owner,
                repo=build.repo_name,
                check_run_id=job.github_check_run_id,
                conclusion=build.conclusion,
                summary=check_summary_body,
                auth_headers=auth_headers,
            )
            github_check_written = True
        elif build.is_update_from_other and build.existing_github_check_run_id is not None:
            job.github_check_run_id = build.existing_github_check_run_id
            await github_api.update_check_run(
                client,
                github_installation_id=installation.github_installation_id,
                owner=build.owner,
                repo=build.repo_name,
                check_run_id=build.existing_github_check_run_id,
                conclusion=build.conclusion,
                summary=check_summary_body,
                auth_headers=auth_headers,
            )
            github_check_written = True
        else:
            check_run_id = await github_api.create_check_run(
                client,
                github_installation_id=installation.github_installation_id,
                owner=build.owner,
                repo=build.repo_name,
                head_sha=job.head_sha,
                external_id=build.external_id,
                conclusion=build.conclusion,
                summary=check_summary_body,
                auth_headers=auth_headers,
            )
            job.github_check_run_id = check_run_id
            github_check_written = True

        if job.github_comment_id is not None:
            await github_api.update_issue_comment(
                client,
                github_installation_id=installation.github_installation_id,
                owner=build.owner,
                repo=build.repo_name,
                comment_id=job.github_comment_id,
                body=issue_comment_body,
                auth_headers=auth_headers,
            )
            github_comment_written = True
        elif build.is_update_from_other and build.existing_github_comment_id is not None:
            job.github_comment_id = build.existing_github_comment_id
            await github_api.update_issue_comment(
                client,
                github_installation_id=installation.github_installation_id,
                owner=build.owner,
                repo=build.repo_name,
                comment_id=build.existing_github_comment_id,
                body=issue_comment_body,
                auth_headers=auth_headers,
            )
            github_comment_written = True
        else:
            comment_id = await github_api.create_issue_comment(
                client,
                github_installation_id=installation.github_installation_id,
                owner=build.owner,
                repo=build.repo_name,
                issue_number=pull_request.number,
                body=issue_comment_body,
                auth_headers=auth_headers,
            )
            job.github_comment_id = comment_id
            github_comment_written = True

        skipped_before_commit = await _recheck_publish_authority_before_flush(
            session,
            job,
            run,
            pull_request,
        )
        if skipped_before_commit is not None:
            await _best_effort_revert_partial_flush_surface(
                client,
                github_installation_id=installation.github_installation_id,
                owner=build.owner,
                repo_name=build.repo_name,
                job=job,
                auth_headers=auth_headers,
                github_check_written=github_check_written,
                github_comment_written=github_comment_written,
                publish_job_id=publish_job_id,
            )
            return skipped_before_commit

        await _commit_publish_job_progress(session)

        skipped_before_inline = await _recheck_publish_authority_before_flush(
            session,
            job,
            run,
            pull_request,
        )
        if skipped_before_inline is not None:
            await _best_effort_revert_partial_flush_surface(
                client,
                github_installation_id=installation.github_installation_id,
                owner=build.owner,
                repo_name=build.repo_name,
                job=job,
                auth_headers=auth_headers,
                github_check_written=github_check_written,
                github_comment_written=github_comment_written,
                publish_job_id=publish_job_id,
            )
            return skipped_before_inline

        inline_thread_ids: dict[str, str] = {}
        inline_written_this_flush: list[int] = []
        inline_422_recovered_count = 0
        inline_422_recovered_fingerprints = set(
            _load_inline_422_recovered_fingerprints(job.summary_json)
        )
        if build.post_inline:
            for spec in build.inline_posts:
                if spec.group_fingerprint in retry_posted:
                    inline_threads[spec.group_fingerprint] = retry_posted[spec.group_fingerprint]
                    continue
                if spec.group_fingerprint in inline_422_recovered_fingerprints:
                    continue
                skipped_during_inline = await _recheck_publish_authority_before_flush(
                    session,
                    job,
                    run,
                    pull_request,
                )
                if skipped_during_inline is not None:
                    await _best_effort_revert_partial_flush_surface(
                        client,
                        github_installation_id=installation.github_installation_id,
                        owner=build.owner,
                        repo_name=build.repo_name,
                        job=job,
                        auth_headers=auth_headers,
                        github_check_written=github_check_written,
                        github_comment_written=github_comment_written,
                        publish_job_id=publish_job_id,
                        inline_comment_ids=inline_written_this_flush,
                    )
                    return skipped_during_inline
                comment_id = await _create_inline_review_comment_with_422_retry(
                    client,
                    github_installation_id=installation.github_installation_id,
                    owner=build.owner,
                    repo_name=build.repo_name,
                    pull_number=pull_request.number,
                    commit_id=job.head_sha,
                    spec=spec,
                    auth_headers=auth_headers,
                )
                if comment_id is None:
                    logger.warning(
                        "github_publish_inline_comment_skipped",
                        extra={
                            "publish_job_id": str(publish_job_id),
                            "file_path": spec.file_path,
                            "line": spec.start_line,
                            "status_code": 422,
                            "recovered": True,
                        },
                    )
                    inline_422_recovered_count += 1
                    inline_422_recovered_fingerprints.add(spec.group_fingerprint)
                    job.summary_json = {
                        **(job.summary_json or {}),
                        _INLINE_422_RECOVERED_FINGERPRINTS_KEY: sorted(
                            inline_422_recovered_fingerprints
                        ),
                    }
                    continue
                inline_threads[spec.group_fingerprint] = comment_id
                inline_written_this_flush.append(comment_id)
                thread_id = thread_index.get(comment_id)
                if isinstance(thread_id, str) and thread_id:
                    inline_thread_ids[spec.group_fingerprint] = thread_id
                job.summary_json = {
                    **(job.summary_json or {}),
                    "github_inline_threads": serialize_inline_thread_map(
                        inline_threads,
                        prior_v2=(job.summary_json or {}).get("github_inline_threads")
                        if isinstance((job.summary_json or {}).get("github_inline_threads"), dict)
                        else build.prior_v2_inline,
                        thread_ids=inline_thread_ids,
                    ),
                }
                await _commit_publish_job_progress(session)
            if inline_422_recovered_fingerprints and build.inline_posts:
                issue_comment_body = await _append_recovered_inline_422_blocks_to_issue_comment(
                    client,
                    github_installation_id=installation.github_installation_id,
                    owner=build.owner,
                    repo_name=build.repo_name,
                    job=job,
                    build=build,
                    issue_comment_body=issue_comment_body,
                    recovered_fingerprints=inline_422_recovered_fingerprints,
                    auth_headers=auth_headers,
                )
            if inline_422_recovered_count:
                job.summary_json = {
                    **(job.summary_json or {}),
                    _INLINE_422_RECOVERED_COUNT_KEY: inline_422_recovered_count,
                    _INLINE_422_RECOVERED_FINGERPRINTS_KEY: sorted(
                        inline_422_recovered_fingerprints
                    ),
                }
            job.inline_comments_posted = all(
                spec.group_fingerprint in inline_threads
                or spec.group_fingerprint in inline_422_recovered_fingerprints
                for spec in build.inline_posts
            )
            if inline_thread_ids:
                job.summary_json = {
                    **(job.summary_json or {}),
                    "github_inline_threads": serialize_inline_thread_map(
                        inline_threads,
                        prior_v2=(job.summary_json or {}).get("github_inline_threads")
                        if isinstance((job.summary_json or {}).get("github_inline_threads"), dict)
                        else build.prior_v2_inline,
                        thread_ids=inline_thread_ids,
                    ),
                }

        await _checkpoint_publish_surface(session, persist=persist_github_surface)
    return None


async def _commit_publish_job_progress(session: AsyncSession) -> None:
    """Commit publish job row so Celery retry survives mid-flush failures."""
    await session.flush()
    await session.commit()


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

    retry_posted_inline = deserialize_inline_thread_map(
        (job.summary_json or {}).get("github_inline_threads")
    )

    try:
        build = await _build_publish_surface(
            session,
            job=job,
            revision=revision,
            pull_request=pull_request,
            repository=repository,
            installation=installation,
        )
        job.summary_json = build.summary_json

        skipped = await _recheck_publish_authority_before_flush(
            session,
            job,
            run,
            pull_request,
        )
        if skipped is not None:
            return skipped

        skipped_mid_flush = await _flush_publish_surface(
            session,
            job=job,
            publish_job_id=publish_job_id,
            build=build,
            pull_request=pull_request,
            installation=installation,
            persist_github_surface=persist_github_surface,
            retry_posted_inline=retry_posted_inline,
            run=run,
        )
        if skipped_mid_flush is not None:
            return skipped_mid_flush

        job.status = GitHubPublishJobStatus.completed
        await session.flush()
        pipeline_run = await get_pipeline_run_for_review_run(
            session, review_run_id=job.review_run_id
        )
        if pipeline_run is not None:
            await record_publish_pipeline_step(
                session,
                pipeline_run_id=pipeline_run.id,
                job=job,
                summary_markdown=build.check_summary,
                issue_comment_markdown=build.issue_comment,
                duration_ms=int((time.monotonic() - started) * 1000),
            )
        return job
    except (httpx.HTTPError, ServiceUnavailableError) as exc:
        if job.status in (
            GitHubPublishJobStatus.skipped_not_head,
            GitHubPublishJobStatus.skipped_superseded,
        ):
            logger.warning(
                "github_publish_job_skip_after_surface_error",
                extra={"publish_job_id": str(publish_job_id), "error": str(exc)},
            )
            return job
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
        if job.status not in _TERMINAL_PUBLISH_JOB_STATUSES:
            job.status = GitHubPublishJobStatus.failed
            job.error_message = str(exc)[:2000]
            await session.flush()
        pipeline_run = await get_pipeline_run_for_review_run(
            session, review_run_id=job.review_run_id
        )
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
