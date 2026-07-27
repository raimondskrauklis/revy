# backend/app/services/github_review.py
"""GitHub PR revision review — R4."""
from __future__ import annotations

import json
from collections import defaultdict
from dataclasses import dataclass
from uuid import UUID

import httpx
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import (
    FindingCategory,
    FindingSeverity,
    GitHubIndexMode,
    GitHubReviewRunStatus,
    ReviewProfile,
    stored_enum_value,
)
from app.core.config import settings
from app.core.exceptions import (
    ConflictError,
    NotFoundError,
    RateLimitedError,
    ServiceUnavailableError,
    ValidationError,
)
from app.core.logging import get_logger
from app.core.worker_retries import classify_transient_error
from app.integrations import llm_dispatch, moonshot_review
from app.integrations.github_api import CompareCommitsResult, CompareFileChange, compare_commits
from app.models.github_finding import GitHubFindingORM
from app.models.github_index_job import GitHubIndexJobORM
from app.models.github_installation import GitHubInstallationORM
from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
from app.models.github_repository import GitHubRepositoryORM
from app.models.github_review_run import GitHubReviewRunORM
from app.schemas.github_indexing import GitHubChunkSearchResult
from app.schemas.github_review import GitHubFindingListResponse, GitHubFindingResponse
from app.services.github_indexing import (
    ensure_revision_access,
    get_latest_completed_index_job,
    index_job_in_progress,
    search_revision_chunks,
)
from app.services.github_suggestion import normalize_end_line, validated_suggestion_for_row
from app.services.model_policy import ModelRef, resolve_model, review_profile_to_model_role

logger = get_logger(__name__)

SEARCH_LENSES = (
    "security vulnerabilities",
    "logic bugs",
    "performance issues",
)
TOP_K_PER_QUERY = 10
SUPPLEMENTAL_CAP_DIFF = 15
SUPPLEMENTAL_CAP_FULL = 30
DIFF_MAX_BYTES = 128 * 1024
PR_BODY_MAX_BYTES = 4 * 1024
FINDING_LIST_DEFAULT_LIMIT = 100
FINDING_LIST_MAX_LIMIT = 500
_FULL_INDEX_PROFILES = frozenset({ReviewProfile.deep, ReviewProfile.critical})


@dataclass(frozen=True)
class ScopedChunkHit:
    hit: GitHubChunkSearchResult
    lens: str
    in_diff: bool
    rank: int


@dataclass(frozen=True)
class ReviewContextPack:
    prompt: str
    manifest: dict


def _review_profile_str(profile: ReviewProfile | str) -> str:
    return profile if isinstance(profile, str) else profile.value


def _truncate_utf8(text: str, max_bytes: int) -> str:
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text
    return encoded[:max_bytes].decode("utf-8", errors="ignore")


def _is_test_path(file_path: str) -> bool:
    normalized = file_path.replace("\\", "/")
    parts = normalized.split("/")
    return "tests" in parts or normalized.startswith("tests/")


def _retrieval_file_paths(changed_files: frozenset[str]) -> frozenset[str]:
    if not changed_files:
        return frozenset()
    if any(_is_test_path(path) for path in changed_files):
        return changed_files
    return frozenset(path for path in changed_files if not _is_test_path(path))


def _patch_entry_size(filename: str, patch: str) -> int:
    return len(filename.encode("utf-8")) + len(patch.encode("utf-8")) + 32


def _format_unified_diff(patches: list[tuple[str, str]]) -> str:
    parts: list[str] = []
    for filename, patch in patches:
        parts.append(f"--- a/{filename}\n+++ b/{filename}\n{patch}")
    return "\n\n".join(parts)


def build_unified_diff(
    files: tuple[CompareFileChange, ...],
    *,
    max_bytes: int = DIFF_MAX_BYTES,
) -> tuple[str, bool, list[str]]:
    patches: list[tuple[str, str]] = []
    for item in files:
        if item.patch:
            patches.append((item.filename, item.patch))

    if not patches:
        return "", False, []

    total_size = sum(_patch_entry_size(name, patch) for name, patch in patches)
    if total_size <= max_bytes:
        return _format_unified_diff(patches), False, []

    kept = list(patches)
    omitted: list[str] = []
    kept.sort(key=lambda entry: len(entry[1]), reverse=True)
    while kept and sum(_patch_entry_size(name, patch) for name, patch in kept) > max_bytes:
        removed_name, _ = kept.pop(0)
        omitted.append(removed_name)

    kept.sort(key=lambda entry: entry[0])
    return _format_unified_diff(kept), True, omitted


def _build_review_prompt(
    *,
    pr_title: str,
    pr_body: str | None,
    head_sha: str,
    base_ref: str,
    head_ref: str,
    index_mode: GitHubIndexMode,
    changed_files: list[str],
    unified_diff: str,
    supplemental: list[ScopedChunkHit],
) -> str:
    parts = [
        "Pull request metadata:",
        f"title: {pr_title}",
        f"head_sha: {head_sha}",
        f"base_ref...head_ref: {base_ref}...{head_ref}",
        f"index_mode: {stored_enum_value(index_mode)}",
    ]
    if pr_body:
        parts.extend(["", "PR body:", _truncate_utf8(pr_body, PR_BODY_MAX_BYTES)])

    parts.extend(["", "Changed files:"])
    if changed_files:
        parts.extend(changed_files)
    else:
        parts.append("(none)")

    parts.extend(["", "Unified diff (primary):"])
    if unified_diff:
        parts.append(unified_diff)
    else:
        parts.append("(empty)")

    if supplemental:
        parts.extend(["", "Supplemental context (bounded):"])
        for item in supplemental:
            chunk = item.hit
            parts.append(
                f"\n--- {chunk.file_path} (chunk {chunk.chunk_index}, "
                f"lens={item.lens}, score={chunk.score:.4f}, in_diff={item.in_diff}, "
                f"rank={item.rank}) ---\n{chunk.content}"
            )

    parts.extend(
        [
            "",
            "Review instruction:",
            "Focus on introduced or changed logic in the unified diff. "
            "Use supplemental context only to validate cross-file impact.",
        ]
    )
    return "\n".join(parts)


def build_retrieval_manifest(
    *,
    index_mode: GitHubIndexMode,
    changed_files: list[str],
    diff_truncated: bool,
    omitted_files: list[str],
    fallback_reason: str | None,
    supplemental: list[ScopedChunkHit],
) -> dict:
    return {
        "index_mode": stored_enum_value(index_mode),
        "changed_files": changed_files,
        "diff_truncated": diff_truncated,
        "omitted_files": omitted_files,
        "fallback_reason": fallback_reason,
        "retrieval_hits": [
            {
                "chunk_id": str(item.hit.id),
                "file_path": item.hit.file_path,
                "chunk_index": item.hit.chunk_index,
                "score": item.hit.score,
                "lens": item.lens,
                "in_diff": item.in_diff,
                "rank": item.rank,
            }
            for item in supplemental
        ],
        "changed_symbols": [],
        "structural_context_mode": "none",
        "caller_files_requested": [],
        "caller_files_included": [],
        "structural_context_attempted": False,
    }


async def create_review_run(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    repository_id: UUID,
    pull_request_id: UUID,
    revision_id: UUID,
    profile: ReviewProfile = ReviewProfile.standard,
) -> GitHubReviewRunORM:
    if not settings.reviewer_llm_enabled():
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

    if await index_job_in_progress(
        session,
        workspace_id=workspace_id,
        revision_id=revision_id,
    ):
        raise ConflictError(
            message="An index job is already in progress for this revision",
            error_code="index_in_progress",
        )

    index_job = await get_latest_completed_index_job(
        session,
        workspace_id=workspace_id,
        revision_id=revision_id,
    )
    if index_job is None:
        raise ConflictError(
            message="Revision must be indexed before review",
            error_code="index_required",
        )

    if profile in _FULL_INDEX_PROFILES and index_job.index_mode != GitHubIndexMode.full:
        raise ConflictError(
            message="Deep/critical review requires a completed full-repo index",
            error_code="index_mode_mismatch",
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

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.pending,
        profile=profile,
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


async def _collect_supplemental_chunks(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    repository_id: UUID,
    pull_request_id: UUID,
    revision_id: UUID,
    pr_title: str,
    changed_files: frozenset[str],
    index_mode: GitHubIndexMode,
    broaden_on_compare_failure: bool = False,
) -> list[ScopedChunkHit]:
    if broaden_on_compare_failure or index_mode == GitHubIndexMode.full:
        cap = SUPPLEMENTAL_CAP_FULL
        file_filter = None
    else:
        cap = SUPPLEMENTAL_CAP_DIFF
        retrieval_paths = _retrieval_file_paths(changed_files)
        file_filter = retrieval_paths
        if not retrieval_paths:
            return []

    queries = [pr_title, *SEARCH_LENSES]
    seen: set[tuple[str, int]] = set()
    merged: list[ScopedChunkHit] = []
    rank = 0

    for lens in queries:
        hits = await search_revision_chunks(
            session,
            workspace_id=workspace_id,
            repository_id=repository_id,
            pull_request_id=pull_request_id,
            revision_id=revision_id,
            query=lens,
            top_k=TOP_K_PER_QUERY,
            file_paths=file_filter,
        )
        for hit in hits:
            key = (hit.file_path, hit.chunk_index)
            if key in seen:
                continue
            seen.add(key)
            rank += 1
            merged.append(
                ScopedChunkHit(
                    hit=hit,
                    lens=lens,
                    in_diff=hit.file_path in changed_files,
                    rank=rank,
                )
            )
            if len(merged) >= cap:
                return merged
    return merged


async def _fetch_compare_for_review(
    session: AsyncSession,
    *,
    revision: GitHubPullRequestRevisionORM,
    pull_request: GitHubPullRequestORM,
) -> tuple[CompareCommitsResult | None, str | None]:
    if not revision.base_sha:
        return None, "missing_base_sha"

    repository = await session.get(GitHubRepositoryORM, pull_request.repository_id)
    installation = await session.get(GitHubInstallationORM, pull_request.installation_id)
    if repository is None or installation is None:
        return None, "repository_or_installation_not_found"

    owner, repo_name = repository.full_name.split("/", 1)
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            compare = await compare_commits(
                client,
                github_installation_id=installation.github_installation_id,
                owner=owner,
                repo=repo_name,
                base_sha=revision.base_sha,
                head_sha=revision.head_sha,
            )
        except (NotFoundError, RateLimitedError, ServiceUnavailableError) as exc:
            return None, exc.error_code
        except httpx.HTTPStatusError as exc:
            return None, f"compare_http_{exc.response.status_code}"
    return compare, None


async def prepare_review_context(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    repository_id: UUID,
    pull_request_id: UUID,
    revision: GitHubPullRequestRevisionORM,
    pull_request: GitHubPullRequestORM,
    index_job: GitHubIndexJobORM,
) -> ReviewContextPack:
    compare, compare_fallback = await _fetch_compare_for_review(
        session,
        revision=revision,
        pull_request=pull_request,
    )

    changed_files: list[str] = []
    unified_diff = ""
    diff_truncated = False
    omitted_files: list[str] = []
    fallback_reason = compare_fallback or index_job.fallback_reason
    broaden_supplemental = False

    if compare is not None:
        changed_files = list(compare.paths_to_index)
        unified_diff, diff_truncated, omitted_files = build_unified_diff(compare.files)
    elif index_job.index_mode == GitHubIndexMode.diff:
        broaden_supplemental = True

    supplemental = await _collect_supplemental_chunks(
        session,
        workspace_id=workspace_id,
        repository_id=repository_id,
        pull_request_id=pull_request_id,
        revision_id=revision.id,
        pr_title=pull_request.title,
        changed_files=frozenset(changed_files),
        index_mode=index_job.index_mode,
        broaden_on_compare_failure=broaden_supplemental,
    )

    prompt = _build_review_prompt(
        pr_title=pull_request.title,
        pr_body=None,
        head_sha=revision.head_sha,
        base_ref=pull_request.base_ref,
        head_ref=pull_request.head_ref,
        index_mode=index_job.index_mode,
        changed_files=changed_files,
        unified_diff=unified_diff,
        supplemental=supplemental,
    )
    manifest = build_retrieval_manifest(
        index_mode=index_job.index_mode,
        changed_files=changed_files,
        diff_truncated=diff_truncated,
        omitted_files=omitted_files,
        fallback_reason=fallback_reason,
        supplemental=supplemental,
    )
    return ReviewContextPack(prompt=prompt, manifest=manifest)


def _parse_finding_row(raw: dict) -> tuple[dict | None, str | None]:
    category_raw = str(raw.get("category", "")).strip().lower()
    if category_raw == FindingCategory.style.value:
        return None, "style_category"

    try:
        severity = FindingSeverity(str(raw.get("severity", "")).strip().lower())
        category = FindingCategory(category_raw)
    except ValueError:
        return None, "invalid_enum"

    title = raw.get("title")
    message = raw.get("message")
    if not isinstance(title, str) or not title.strip():
        return None, "missing_title"
    if not isinstance(message, str) or not message.strip():
        return None, "missing_message"

    file_path = raw.get("file_path")
    start_line = raw.get("start_line")
    end_line = raw.get("end_line")
    normalized_end_line = normalize_end_line(int(end_line) if isinstance(end_line, int) else None)
    normalized_start_line = int(start_line) if isinstance(start_line, int) else None
    if normalized_start_line == 0:
        normalized_start_line = None

    parsed_file_path = (
        file_path.strip() if isinstance(file_path, str) and file_path.strip() else None
    )
    suggestion = validated_suggestion_for_row(
        suggestion=raw.get("suggestion"),
        file_path=parsed_file_path,
        start_line=normalized_start_line,
        end_line=normalized_end_line,
    )

    row = {
        "severity": severity,
        "category": category,
        "title": title.strip(),
        "message": message.strip(),
        "file_path": parsed_file_path,
        "start_line": normalized_start_line,
        "end_line": normalized_end_line,
    }
    if suggestion is not None:
        row["suggestion"] = suggestion
    return row, None


def parse_finding_rows(raw_findings: list) -> tuple[list[dict], dict]:
    parsed_rows: list[dict] = []
    drop_counts: dict[str, int] = defaultdict(int)

    for item in raw_findings:
        if not isinstance(item, dict):
            drop_counts["invalid_row"] += 1
            continue
        row, reason = _parse_finding_row(item)
        if row is None:
            drop_counts[reason or "unknown"] += 1
            continue
        parsed_rows.append(row)

    dropped_count = sum(drop_counts.values())
    return parsed_rows, {
        "parsed_count": len(parsed_rows),
        "dropped_count": dropped_count,
        "drop_reasons": dict(drop_counts),
    }


async def _call_llm(*, model_ref: ModelRef, profile: str, prompt: str) -> str:
    timeout = float(settings.revy_revision_timeout_seconds(profile))
    async with httpx.AsyncClient(timeout=timeout) as client:
        return await llm_dispatch.call_review_llm(
            client,
            model_ref=model_ref,
            profile=profile,
            user_prompt=prompt,
            timeout_seconds=timeout,
        )


async def run_review_run(session: AsyncSession, *, review_run_id: UUID) -> GitHubReviewRunORM:
    run = await session.get(GitHubReviewRunORM, review_run_id)
    if run is None:
        raise NotFoundError("Review run not found")

    if run.status != GitHubReviewRunStatus.pending:
        logger.info(
            "github_review_run_skip_non_pending",
            extra={"review_run_id": str(review_run_id), "status": str(run.status)},
        )
        return run

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

    index_job = await get_latest_completed_index_job(
        session,
        workspace_id=run.workspace_id,
        revision_id=run.revision_id,
    )
    if index_job is None:
        run.status = GitHubReviewRunStatus.failed
        run.error_message = "index_required"
        await session.flush()
        return run

    try:
        context_pack = await prepare_review_context(
            session,
            workspace_id=run.workspace_id,
            repository_id=repository_id,
            pull_request_id=pull_request_id,
            revision=revision,
            pull_request=pull_request,
            index_job=index_job,
        )
        prompt = context_pack.prompt
        model_role = review_profile_to_model_role(_review_profile_str(run.profile))
        model_ref = await resolve_model(session, run.workspace_id, model_role)
        run.provider = model_ref.provider
        run.model_id = model_ref.model_id
        await session.flush()

        raw_json = await _call_llm(
            model_ref=model_ref,
            profile=_review_profile_str(run.profile),
            prompt=prompt,
        )

        try:
            raw_findings = moonshot_review.parse_review_json(raw_json)
        except (json.JSONDecodeError, ValueError) as exc:
            run.status = GitHubReviewRunStatus.failed
            run.error_message = str(exc)[:2000]
            await session.flush()
            return run

        parsed_rows, _parse_report = parse_finding_rows(raw_findings)

        await session.execute(
            delete(GitHubFindingORM).where(GitHubFindingORM.review_run_id == run.id)
        )

        for parsed in parsed_rows:
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
    except ValidationError as exc:
        logger.error(
            "github_review_run_failed",
            extra={"review_run_id": str(review_run_id), "error": str(exc)},
        )
        run.status = GitHubReviewRunStatus.failed
        run.error_message = str(exc)[:2000]
        await session.flush()
        return run
    except (httpx.HTTPError, ServiceUnavailableError) as exc:
        retryable = classify_transient_error(exc)
        if retryable is not None:
            logger.warning(
                "github_review_run_transient_failure",
                extra={"review_run_id": str(review_run_id), "error": str(exc)},
            )
            raise retryable from exc
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
