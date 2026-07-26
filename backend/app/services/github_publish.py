# backend/app/services/github_publish.py
"""GitHub publish pipeline — R6."""
from __future__ import annotations

from uuid import UUID

import httpx
from sqlalchemy import case, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import (
    FindingSeverity,
    GitHubFindingGroupState,
    GitHubPublishJobStatus,
    GitHubReviewRunStatus,
)
from app.core.config import settings
from app.core.exceptions import ConflictError, NotFoundError, ServiceUnavailableError
from app.core.logging import get_logger
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
from app.services.github_indexing import ensure_revision_access

logger = get_logger(__name__)

SUMMARY_ROW_CAP = 50

_PUBLISH_GROUP_SEVERITY_ORDER = case(
    (GitHubFindingGroupORM.severity == FindingSeverity.critical, 0),
    (GitHubFindingGroupORM.severity == FindingSeverity.error, 1),
    (GitHubFindingGroupORM.severity == FindingSeverity.warning, 2),
    else_=3,
)


class PublishJobRetryableError(Exception):
    """Transient publish failure — Celery should retry after persisting progress."""


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
    active = [g for g in groups if g.state == GitHubFindingGroupState.active]
    if any(g.severity in (FindingSeverity.error, FindingSeverity.critical) for g in active):
        return "failure"
    if not active:
        return "success"
    if all(g.severity in (FindingSeverity.warning, FindingSeverity.info) for g in active):
        return "neutral"
    return "success"


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
            f"| {group.severity.value} | {group.category.value} | {title_cell} | {file_cell} |"
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
                (FindingSeverity.error, FindingSeverity.critical),
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
        )
        .order_by(GitHubPublishJobORM.created_at.desc())
        .limit(1)
    )


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
    job = await session.get(GitHubPublishJobORM, publish_job_id)
    if job is None:
        raise NotFoundError("Publish job not found")

    job.status = GitHubPublishJobStatus.processing
    job.error_message = None
    await session.flush()

    run = await session.get(GitHubReviewRunORM, job.review_run_id)
    revision = await session.get(GitHubPullRequestRevisionORM, job.revision_id)
    if run is None or revision is None:
        job.status = GitHubPublishJobStatus.failed
        job.error_message = "review_run_or_revision_not_found"
        await session.flush()
        return job

    pull_request = await session.get(GitHubPullRequestORM, revision.pull_request_id)
    repository = await session.get(GitHubRepositoryORM, pull_request.repository_id) if pull_request else None
    installation = (
        await session.get(GitHubInstallationORM, pull_request.installation_id) if pull_request else None
    )
    if pull_request is None or repository is None or installation is None:
        job.status = GitHubPublishJobStatus.failed
        job.error_message = "pull_request_context_not_found"
        await session.flush()
        return job

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
    summary = build_summary_markdown(pull_request_id=pull_request.id, groups=groups)
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
                    summary=summary,
                    auth_headers=auth_headers,
                )
                if job.github_comment_id is not None:
                    await github_api.update_issue_comment(
                        client,
                        github_installation_id=installation.github_installation_id,
                        owner=owner,
                        repo=repo_name,
                        comment_id=job.github_comment_id,
                        body=summary,
                        auth_headers=auth_headers,
                    )
                else:
                    comment_id = await github_api.create_issue_comment(
                        client,
                        github_installation_id=installation.github_installation_id,
                        owner=owner,
                        repo=repo_name,
                        issue_number=pull_request.number,
                        body=summary,
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
                    summary=summary,
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
                        body=summary,
                        auth_headers=auth_headers,
                    )
                else:
                    comment_id = await github_api.create_issue_comment(
                        client,
                        github_installation_id=installation.github_installation_id,
                        owner=owner,
                        repo=repo_name,
                        issue_number=pull_request.number,
                        body=summary,
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
                    summary=summary,
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
                    body=summary,
                    auth_headers=auth_headers,
                )
                job.github_comment_id = comment_id
                await _checkpoint_publish_surface(session, persist=persist_github_surface)

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
                    try:
                        await github_api.create_pull_request_review_comment(
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
                                severity=finding.severity.value,
                            ),
                            auth_headers=auth_headers,
                        )
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
                job.inline_comments_posted = True
                await _checkpoint_publish_surface(session, persist=persist_github_surface)

        job.status = GitHubPublishJobStatus.completed
        await session.flush()
        return job
    except (httpx.HTTPError, ServiceUnavailableError) as exc:
        logger.error(
            "github_publish_job_failed",
            extra={"publish_job_id": str(publish_job_id), "error": str(exc)},
        )
        if not persist_github_surface:
            job.status = GitHubPublishJobStatus.failed
            job.error_message = str(exc)[:2000]
            await session.flush()
        raise PublishJobRetryableError(str(exc)) from exc
