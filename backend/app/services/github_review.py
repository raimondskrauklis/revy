# backend/app/services/github_review.py
"""GitHub PR revision review — R4."""
from __future__ import annotations

import json
from uuid import UUID

import httpx
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import (
    FindingCategory,
    FindingSeverity,
    GitHubIndexJobStatus,
    GitHubReviewRunStatus,
    ReviewProfile,
)
from app.core.config import settings
from app.core.exceptions import ConflictError, NotFoundError, ServiceUnavailableError
from app.core.logging import get_logger
from app.integrations import anthropic_review, moonshot_review
from app.models.github_finding import GitHubFindingORM
from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
from app.models.github_review_run import GitHubReviewRunORM
from app.schemas.github_indexing import GitHubChunkSearchResult
from app.schemas.github_review import GitHubFindingListResponse, GitHubFindingResponse
from app.services.github_indexing import (
    ensure_revision_access,
    get_latest_index_job,
    search_revision_chunks,
)

logger = get_logger(__name__)

SEARCH_LENSES = (
    "security vulnerabilities",
    "logic bugs",
    "performance issues",
)
CONTEXT_CHUNK_CAP = 30
TOP_K_PER_QUERY = 10
FINDING_LIST_DEFAULT_LIMIT = 100
FINDING_LIST_MAX_LIMIT = 500


async def create_review_run(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    repository_id: UUID,
    pull_request_id: UUID,
    revision_id: UUID,
    profile: ReviewProfile = ReviewProfile.standard,
) -> GitHubReviewRunORM:
    if not settings.llm_enabled:
        raise ServiceUnavailableError(
            message="LLM API is not configured",
            error_code="llm_disabled",
        )
    if not settings.embeddings_enabled:
        raise ServiceUnavailableError(
            message="Embeddings API is not configured",
            error_code="embeddings_disabled",
        )
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

    index_job = await get_latest_index_job(
        session,
        workspace_id=workspace_id,
        revision_id=revision_id,
    )
    if index_job is None or index_job.status != GitHubIndexJobStatus.completed:
        raise ConflictError(
            message="Revision must be indexed before review",
            error_code="index_required",
        )

    in_progress = await session.scalar(
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
    if in_progress is not None:
        raise ConflictError(
            message="A review is already in progress for this revision",
            error_code="review_in_progress",
        )

    provider = (settings.revy_llm_provider or "moonshot").strip().lower()
    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.pending,
        profile=profile,
        provider=provider,
    )
    session.add(run)
    await session.flush()
    return run


def enqueue_review_run(review_run_id: UUID, *, profile: ReviewProfile) -> None:
    from app.workers.review_tasks import review_pull_request_revision

    timeout = settings.revy_revision_timeout_seconds(profile.value)
    review_pull_request_revision.apply_async(
        args=[str(review_run_id)],
        queue="review",
        soft_time_limit=timeout,
        time_limit=timeout + 60,
    )


async def _collect_context_chunks(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    repository_id: UUID,
    pull_request_id: UUID,
    revision_id: UUID,
    pr_title: str,
) -> list[GitHubChunkSearchResult]:
    queries = [pr_title, *SEARCH_LENSES]
    seen: set[tuple[str, int]] = set()
    merged: list[GitHubChunkSearchResult] = []

    for query in queries:
        hits = await search_revision_chunks(
            session,
            workspace_id=workspace_id,
            repository_id=repository_id,
            pull_request_id=pull_request_id,
            revision_id=revision_id,
            query=query,
            top_k=TOP_K_PER_QUERY,
        )
        for hit in hits:
            key = (hit.file_path, hit.chunk_index)
            if key in seen:
                continue
            seen.add(key)
            merged.append(hit)
            if len(merged) >= CONTEXT_CHUNK_CAP:
                return merged
    return merged


def _build_review_prompt(*, pr_title: str, chunks: list[GitHubChunkSearchResult]) -> str:
    parts = [f"Pull request title: {pr_title}", "", "Code context:"]
    for chunk in chunks:
        parts.append(f"\n--- {chunk.file_path} (chunk {chunk.chunk_index}) ---\n{chunk.content}")
    return "\n".join(parts)


def _parse_finding_row(raw: dict) -> dict | None:
    category_raw = str(raw.get("category", "")).strip().lower()
    if category_raw == FindingCategory.style.value:
        return None

    try:
        severity = FindingSeverity(str(raw.get("severity", "")).strip().lower())
        category = FindingCategory(category_raw)
    except ValueError:
        return None

    title = raw.get("title")
    message = raw.get("message")
    if not isinstance(title, str) or not title.strip():
        return None
    if not isinstance(message, str) or not message.strip():
        return None

    file_path = raw.get("file_path")
    start_line = raw.get("start_line")
    end_line = raw.get("end_line")

    return {
        "severity": severity,
        "category": category,
        "title": title.strip(),
        "message": message.strip(),
        "file_path": file_path.strip() if isinstance(file_path, str) and file_path.strip() else None,
        "start_line": int(start_line) if isinstance(start_line, int) else None,
        "end_line": int(end_line) if isinstance(end_line, int) else None,
    }


async def _call_llm(*, profile: str, prompt: str) -> str:
    provider = (settings.revy_llm_provider or "moonshot").strip().lower()
    timeout = float(settings.revy_revision_timeout_seconds(profile))
    async with httpx.AsyncClient(timeout=timeout) as client:
        if provider == "anthropic":
            return await anthropic_review.complete_review(
                client,
                user_prompt=prompt,
                timeout_seconds=timeout,
            )
        return await moonshot_review.complete_review(
            client,
            profile=profile,
            user_prompt=prompt,
            timeout_seconds=timeout,
        )


async def run_review_run(session: AsyncSession, *, review_run_id: UUID) -> GitHubReviewRunORM:
    run = await session.get(GitHubReviewRunORM, review_run_id)
    if run is None:
        raise NotFoundError("Review run not found")

    run.status = GitHubReviewRunStatus.processing
    run.error_message = None
    await session.flush()

    revision = await session.get(GitHubPullRequestRevisionORM, run.revision_id)
    if revision is None:
        run.status = GitHubReviewRunStatus.failed
        run.error_message = "revision_not_found"
        await session.flush()
        return run

    pull_request = await session.get(GitHubPullRequestORM, revision.pull_request_id)
    if pull_request is None:
        run.status = GitHubReviewRunStatus.failed
        run.error_message = "pull_request_not_found"
        await session.flush()
        return run

    repository_id = pull_request.repository_id
    pull_request_id = pull_request.id

    try:
        chunks = await _collect_context_chunks(
            session,
            workspace_id=run.workspace_id,
            repository_id=repository_id,
            pull_request_id=pull_request_id,
            revision_id=run.revision_id,
            pr_title=pull_request.title,
        )
        prompt = _build_review_prompt(pr_title=pull_request.title, chunks=chunks)
        raw_json = await _call_llm(profile=run.profile.value, prompt=prompt)

        try:
            raw_findings = moonshot_review.parse_review_json(raw_json)
        except (json.JSONDecodeError, ValueError) as exc:
            run.status = GitHubReviewRunStatus.failed
            run.error_message = str(exc)[:2000]
            await session.flush()
            return run

        await session.execute(
            delete(GitHubFindingORM).where(GitHubFindingORM.review_run_id == run.id)
        )

        for item in raw_findings:
            parsed = _parse_finding_row(item)
            if parsed is None:
                continue
            session.add(
                GitHubFindingORM(
                    review_run_id=run.id,
                    workspace_id=run.workspace_id,
                    **parsed,
                )
            )

        run.status = GitHubReviewRunStatus.completed
        await session.flush()
        return run
    except (httpx.HTTPError, ServiceUnavailableError) as exc:
        logger.error(
            "github_review_run_failed",
            extra={"review_run_id": str(review_run_id), "error": str(exc)},
        )
        run.status = GitHubReviewRunStatus.failed
        run.error_message = str(exc)[:2000]
        await session.flush()
        return run


async def get_latest_review_run(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    revision_id: UUID,
) -> GitHubReviewRunORM | None:
    return await session.scalar(
        select(GitHubReviewRunORM)
        .where(
            GitHubReviewRunORM.workspace_id == workspace_id,
            GitHubReviewRunORM.revision_id == revision_id,
        )
        .order_by(GitHubReviewRunORM.created_at.desc())
        .limit(1)
    )


async def get_latest_completed_review_run(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    revision_id: UUID,
) -> GitHubReviewRunORM | None:
    return await session.scalar(
        select(GitHubReviewRunORM)
        .where(
            GitHubReviewRunORM.workspace_id == workspace_id,
            GitHubReviewRunORM.revision_id == revision_id,
            GitHubReviewRunORM.status == GitHubReviewRunStatus.completed,
        )
        .order_by(GitHubReviewRunORM.created_at.desc())
        .limit(1)
    )


async def mark_review_run_failed(
    session: AsyncSession,
    *,
    review_run_id: UUID,
    error_message: str,
) -> None:
    run = await session.get(GitHubReviewRunORM, review_run_id)
    if run is None:
        return
    if run.status in (GitHubReviewRunStatus.completed, GitHubReviewRunStatus.failed):
        return
    run.status = GitHubReviewRunStatus.failed
    run.error_message = error_message[:2000]
    await session.flush()


async def list_review_findings(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    repository_id: UUID,
    pull_request_id: UUID,
    revision_id: UUID,
    limit: int = FINDING_LIST_DEFAULT_LIMIT,
    offset: int = 0,
) -> GitHubFindingListResponse:
    await ensure_revision_access(
        session,
        workspace_id=workspace_id,
        repository_id=repository_id,
        pull_request_id=pull_request_id,
        revision_id=revision_id,
    )

    run = await get_latest_completed_review_run(
        session,
        workspace_id=workspace_id,
        revision_id=revision_id,
    )
    if run is None:
        return GitHubFindingListResponse(items=[], offset=offset, limit=limit, has_more=False)

    rows = list(
        await session.scalars(
            select(GitHubFindingORM)
            .where(
                GitHubFindingORM.workspace_id == workspace_id,
                GitHubFindingORM.review_run_id == run.id,
            )
            .order_by(GitHubFindingORM.created_at)
            .offset(offset)
            .limit(limit + 1)
        )
    )
    has_more = len(rows) > limit
    if has_more:
        rows = rows[:limit]

    return GitHubFindingListResponse(
        items=[GitHubFindingResponse.model_validate(row) for row in rows],
        offset=offset,
        limit=limit,
        has_more=has_more,
    )
