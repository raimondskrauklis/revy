# backend/app/services/github_indexing.py
"""GitHub PR revision indexing — R3."""
from __future__ import annotations

import hashlib
import math
import shutil
from pathlib import Path
from uuid import UUID

import httpx
from sqlalchemy import delete, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import (
    GitHubIndexJobStatus,
    GitHubIndexJobTriggerSource,
    GitHubIndexMode,
    ReviewProfile,
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
from app.integrations.github_api import compare_commits
from app.integrations.github_archive import (
    download_repository_tarball,
    extract_tarball,
    iter_indexable_files,
)
from app.integrations.voyage_embeddings import BATCH_SIZE, embed_query, embed_texts
from app.models.github_code_chunk import GitHubCodeChunkORM
from app.models.github_index_job import GitHubIndexJobORM
from app.models.github_installation import GitHubInstallationORM
from app.models.github_pull_request import (
    GitHubPullRequestORM,
    GitHubPullRequestRevisionORM,
)
from app.models.github_repository import GitHubRepositoryORM
from app.schemas.github_indexing import (
    GitHubChunkSearchResult,
    GitHubCodeChunkListResponse,
    GitHubCodeChunkResponse,
)
from app.services.code_chunking import chunk_file_content

logger = get_logger(__name__)

CHUNK_LIST_DEFAULT_LIMIT = 100
CHUNK_LIST_MAX_LIMIT = 500

_FULL_INDEX_PROFILES = frozenset({ReviewProfile.deep, ReviewProfile.critical})


async def index_job_in_progress(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    revision_id: UUID,
) -> bool:
    existing = await session.scalar(
        select(GitHubIndexJobORM.id)
        .where(
            GitHubIndexJobORM.workspace_id == workspace_id,
            GitHubIndexJobORM.revision_id == revision_id,
            GitHubIndexJobORM.status.in_(
                (GitHubIndexJobStatus.pending, GitHubIndexJobStatus.processing),
            ),
        )
        .limit(1)
    )
    return existing is not None


async def ensure_revision_access(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    repository_id: UUID,
    pull_request_id: UUID,
    revision_id: UUID,
) -> None:
    revision_key = await session.scalar(
        select(GitHubPullRequestRevisionORM.id)
        .join(
            GitHubPullRequestORM,
            GitHubPullRequestRevisionORM.pull_request_id == GitHubPullRequestORM.id,
        )
        .join(
            GitHubRepositoryORM,
            GitHubPullRequestORM.repository_id == GitHubRepositoryORM.id,
        )
        .where(
            GitHubPullRequestRevisionORM.id == revision_id,
            GitHubPullRequestRevisionORM.pull_request_id == pull_request_id,
            GitHubPullRequestORM.repository_id == repository_id,
            GitHubPullRequestORM.workspace_id == workspace_id,
            GitHubRepositoryORM.id == repository_id,
            GitHubRepositoryORM.workspace_id == workspace_id,
        )
    )
    if revision_key is None:
        raise NotFoundError("Pull request revision not found")


async def create_index_job(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    repository_id: UUID,
    pull_request_id: UUID,
    revision_id: UUID,
    index_mode: GitHubIndexMode | None = None,
    index_incremental: bool = True,
) -> GitHubIndexJobORM:
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

    job = GitHubIndexJobORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubIndexJobStatus.pending,
        trigger_source=GitHubIndexJobTriggerSource.manual,
        index_mode=index_mode or GitHubIndexMode.full,
        index_incremental=index_incremental,
    )
    session.add(job)
    await session.flush()
    return job


def enqueue_index_job(index_job_id: UUID) -> None:
    from app.workers.index_tasks import index_pull_request_revision

    index_pull_request_revision.delay(str(index_job_id))


async def prepare_full_index_for_review_profile(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    repository_id: UUID,
    pull_request_id: UUID,
    revision_id: UUID,
    profile: ReviewProfile,
) -> GitHubIndexJobORM | None:
    """Enqueue a full index when deep/critical review needs it. Returns job or None if ready."""
    if profile not in _FULL_INDEX_PROFILES:
        return None

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
    if (
        index_job is not None
        and index_job.index_mode == GitHubIndexMode.full
    ):
        return None

    return await create_index_job(
        session,
        workspace_id=workspace_id,
        repository_id=repository_id,
        pull_request_id=pull_request_id,
        revision_id=revision_id,
        index_mode=GitHubIndexMode.full,
        index_incremental=False,
    )


async def mark_index_job_failed(
    session: AsyncSession,
    *,
    index_job_id: UUID,
    error_message: str,
) -> None:
    job = await session.get(GitHubIndexJobORM, index_job_id)
    if job is None:
        return
    if job.status == GitHubIndexJobStatus.completed:
        return
    job.status = GitHubIndexJobStatus.failed
    job.error_message = error_message[:2000]
    await session.flush()


async def _revision_chunk_count(session: AsyncSession, *, revision_id: UUID) -> int:
    count = await session.scalar(
        select(func.count())
        .select_from(GitHubCodeChunkORM)
        .where(GitHubCodeChunkORM.revision_id == revision_id)
    )
    return int(count or 0)


async def _set_full_mode_warning(
    session: AsyncSession,
    job: GitHubIndexJobORM,
    *,
    file_count: int,
) -> None:
    duration_note = ""
    p50_seconds = await session.scalar(
        select(
            func.percentile_cont(0.5).within_group(
                func.extract(
                    "epoch",
                    GitHubIndexJobORM.updated_at - GitHubIndexJobORM.created_at,
                )
            )
        ).where(
            GitHubIndexJobORM.workspace_id == job.workspace_id,
            GitHubIndexJobORM.index_mode == GitHubIndexMode.full,
            GitHubIndexJobORM.status == GitHubIndexJobStatus.completed,
            GitHubIndexJobORM.id != job.id,
        )
    )
    if p50_seconds is not None:
        duration_note = f" Typical full index duration ~{int(float(p50_seconds))}s (p50)."
    job.warning_message = f"Full-repo index: {file_count} file(s).{duration_note}"[:2000]


def _hash_chunk_content(content: str) -> str:
    return hashlib.sha256(content.encode("utf-8")).hexdigest()


async def _get_parent_revision(
    session: AsyncSession,
    revision: GitHubPullRequestRevisionORM,
) -> GitHubPullRequestRevisionORM | None:
    if revision.revision_number <= 1:
        return None
    return await session.scalar(
        select(GitHubPullRequestRevisionORM).where(
            GitHubPullRequestRevisionORM.pull_request_id == revision.pull_request_id,
            GitHubPullRequestRevisionORM.revision_number == revision.revision_number - 1,
        )
    )


async def _load_parent_chunks(
    session: AsyncSession,
    *,
    parent_revision_id: UUID,
) -> dict[tuple[str, int], GitHubCodeChunkORM]:
    rows = await session.scalars(
        select(GitHubCodeChunkORM).where(GitHubCodeChunkORM.revision_id == parent_revision_id)
    )
    return {(chunk.file_path, chunk.chunk_index): chunk for chunk in rows}


def _set_index_manifest_stats(
    job: GitHubIndexJobORM,
    *,
    reused_count: int,
    new_count: int,
    embed_batches: int,
) -> None:
    job.index_manifest_stats = {
        "reused_count": reused_count,
        "new_count": new_count,
        "embed_batches": embed_batches,
    }


def _parent_chunk_hash(chunk: GitHubCodeChunkORM) -> str:
    return chunk.content_hash or _hash_chunk_content(chunk.content)


def _collect_chunks_for_paths(
    root_dir: Path,
    paths: set[str] | None,
) -> tuple[list[tuple[str, int, str]], int]:
    raw_chunks: list[tuple[str, int, str]] = []
    file_count = 0
    for file_path, content in iter_indexable_files(root_dir):
        file_count += 1
        if paths is not None and file_path not in paths:
            continue
        for chunk in chunk_file_content(file_path, content):
            raw_chunks.append((chunk.file_path, chunk.chunk_index, chunk.content))
    return raw_chunks, file_count


async def run_index_job(session: AsyncSession, *, index_job_id: UUID) -> GitHubIndexJobORM:
    job = await session.get(GitHubIndexJobORM, index_job_id)
    if job is None:
        raise NotFoundError("Index job not found")

    if job.status != GitHubIndexJobStatus.pending:
        logger.info(
            "github_index_job_skip_non_pending",
            extra={"index_job_id": str(index_job_id), "status": stored_enum_value(job.status)},
        )
        return job

    job.status = GitHubIndexJobStatus.processing
    job.error_message = None
    await session.flush()

    revision = await session.get(GitHubPullRequestRevisionORM, job.revision_id)
    if revision is None:
        job.status = GitHubIndexJobStatus.failed
        job.error_message = "revision_not_found"
        await session.flush()
        return job

    pull_request = await session.get(GitHubPullRequestORM, revision.pull_request_id)
    if pull_request is None:
        job.status = GitHubIndexJobStatus.failed
        job.error_message = "pull_request_not_found"
        await session.flush()
        return job

    repository = await session.get(GitHubRepositoryORM, pull_request.repository_id)
    installation = await session.get(GitHubInstallationORM, pull_request.installation_id)
    if repository is None or installation is None:
        job.status = GitHubIndexJobStatus.failed
        job.error_message = "repository_or_installation_not_found"
        await session.flush()
        return job

    work_dir = Path(settings.revy_worktrees_path) / str(job.revision_id)
    try:
        owner, repo_name = repository.full_name.split("/", 1)
        paths_to_index: set[str] | None = None
        paths_to_remove: list[str] = []
        use_diff = job.index_mode == GitHubIndexMode.diff

        async with httpx.AsyncClient(timeout=120.0) as client:
            if use_diff:
                if not revision.base_sha:
                    job.index_mode = GitHubIndexMode.full
                    job.fallback_reason = "missing_base_sha"
                    use_diff = False
                else:
                    try:
                        compare = await compare_commits(
                            client,
                            github_installation_id=installation.github_installation_id,
                            owner=owner,
                            repo=repo_name,
                            base_sha=revision.base_sha,
                            head_sha=revision.head_sha,
                        )
                        paths_to_index = set(compare.paths_to_index)
                        paths_to_remove = list(compare.paths_to_remove)
                    except (NotFoundError, RateLimitedError, ServiceUnavailableError) as exc:
                        job.index_mode = GitHubIndexMode.full
                        job.fallback_reason = exc.error_code
                        use_diff = False
                    except httpx.HTTPStatusError as exc:
                        job.index_mode = GitHubIndexMode.full
                        job.fallback_reason = f"compare_http_{exc.response.status_code}"
                        use_diff = False

            archive_bytes = await download_repository_tarball(
                client,
                github_installation_id=installation.github_installation_id,
                owner=owner,
                repo=repo_name,
                ref=revision.head_sha,
            )

        if work_dir.exists():
            shutil.rmtree(work_dir)
        root_dir = extract_tarball(archive_bytes, work_dir)

        if use_diff and paths_to_index is not None:
            path_filter = paths_to_index
        else:
            path_filter = None

        raw_chunks, indexed_file_count = _collect_chunks_for_paths(root_dir, path_filter)

        parent_chunks: dict[tuple[str, int], GitHubCodeChunkORM] = {}
        if job.index_incremental:
            parent_revision = await _get_parent_revision(session, revision)
            if parent_revision is not None:
                parent_chunks = await _load_parent_chunks(
                    session,
                    parent_revision_id=parent_revision.id,
                )

        changed_paths: set[str] = paths_to_index if (use_diff and paths_to_index is not None) else set()
        removed_paths = set(paths_to_remove) if use_diff else set()
        reused_count = 0
        new_count = 0
        embed_batches = 0

        if use_diff and paths_to_remove:
            await session.execute(
                delete(GitHubCodeChunkORM).where(
                    GitHubCodeChunkORM.revision_id == job.revision_id,
                    GitHubCodeChunkORM.file_path.in_(paths_to_remove),
                )
            )

        if use_diff and paths_to_index is not None:
            if paths_to_index:
                await session.execute(
                    delete(GitHubCodeChunkORM).where(
                        GitHubCodeChunkORM.revision_id == job.revision_id,
                        GitHubCodeChunkORM.file_path.in_(paths_to_index),
                    )
                )
        elif not job.index_incremental or not parent_chunks:
            await session.execute(
                delete(GitHubCodeChunkORM).where(GitHubCodeChunkORM.revision_id == job.revision_id)
            )

        if job.index_incremental and parent_chunks and changed_paths:
            for (file_path, chunk_index), parent_chunk in parent_chunks.items():
                if file_path in changed_paths or file_path in removed_paths:
                    continue
                content_hash = _parent_chunk_hash(parent_chunk)
                session.add(
                    GitHubCodeChunkORM(
                        index_job_id=job.id,
                        revision_id=job.revision_id,
                        workspace_id=job.workspace_id,
                        file_path=file_path,
                        chunk_index=chunk_index,
                        content=parent_chunk.content,
                        content_hash=content_hash,
                        embedding=parent_chunk.embedding,
                    )
                )
                reused_count += 1

        chunks_to_embed: list[tuple[str, int, str, str]] = []
        for file_path, chunk_index, content in raw_chunks:
            content_hash = _hash_chunk_content(content)
            parent_chunk = parent_chunks.get((file_path, chunk_index))
            if (
                job.index_incremental
                and parent_chunk is not None
                and _parent_chunk_hash(parent_chunk) == content_hash
                and parent_chunk.embedding is not None
            ):
                session.add(
                    GitHubCodeChunkORM(
                        index_job_id=job.id,
                        revision_id=job.revision_id,
                        workspace_id=job.workspace_id,
                        file_path=file_path,
                        chunk_index=chunk_index,
                        content=content,
                        content_hash=content_hash,
                        embedding=parent_chunk.embedding,
                    )
                )
                reused_count += 1
                continue
            chunks_to_embed.append((file_path, chunk_index, content, content_hash))

        if chunks_to_embed:
            texts = [item[2] for item in chunks_to_embed]
            async with httpx.AsyncClient(timeout=120.0) as client:
                embeddings = await embed_texts(client, texts)

            if len(embeddings) != len(chunks_to_embed):
                raise RuntimeError("embedding_count_mismatch")

            embed_batches = math.ceil(len(texts) / BATCH_SIZE) if texts else 0
            for (file_path, chunk_index, content, content_hash), embedding in zip(
                chunks_to_embed,
                embeddings,
                strict=True,
            ):
                session.add(
                    GitHubCodeChunkORM(
                        index_job_id=job.id,
                        revision_id=job.revision_id,
                        workspace_id=job.workspace_id,
                        file_path=file_path,
                        chunk_index=chunk_index,
                        content=content,
                        content_hash=content_hash,
                        embedding=embedding,
                    )
                )
                new_count += 1

        if not raw_chunks and not reused_count:
            if use_diff:
                stale_paths = list(paths_to_remove)
                if paths_to_index:
                    stale_paths.extend(paths_to_index)
                if stale_paths:
                    await session.execute(
                        delete(GitHubCodeChunkORM).where(
                            GitHubCodeChunkORM.revision_id == job.revision_id,
                            GitHubCodeChunkORM.file_path.in_(stale_paths),
                        )
                    )
            elif not job.index_incremental or not parent_chunks:
                await session.execute(
                    delete(GitHubCodeChunkORM).where(GitHubCodeChunkORM.revision_id == job.revision_id)
                )

        _set_index_manifest_stats(
            job,
            reused_count=reused_count,
            new_count=new_count,
            embed_batches=embed_batches,
        )
        job.status = GitHubIndexJobStatus.completed
        job.chunk_count = await _revision_chunk_count(session, revision_id=job.revision_id)
        if job.index_mode == GitHubIndexMode.full:
            await _set_full_mode_warning(session, job, file_count=indexed_file_count)
        await session.flush()
        return job
    except httpx.HTTPStatusError as exc:
        logger.error(
            "github_index_job_failed",
            extra={
                "index_job_id": str(index_job_id),
                "error": str(exc),
                "status_code": exc.response.status_code,
            },
        )
        job.status = GitHubIndexJobStatus.failed
        job.error_message = str(exc)[:2000]
        await session.flush()
        return job
    except httpx.TimeoutException as exc:
        logger.error(
            "github_index_job_failed",
            extra={"index_job_id": str(index_job_id), "error": str(exc)},
        )
        job.status = GitHubIndexJobStatus.failed
        job.error_message = str(exc)[:2000]
        await session.flush()
        return job
    except (OSError, RuntimeError, httpx.HTTPError, ServiceUnavailableError) as exc:
        logger.error("github_index_job_failed", extra={"index_job_id": str(index_job_id), "error": str(exc)})
        job.status = GitHubIndexJobStatus.failed
        job.error_message = str(exc)[:2000]
        await session.flush()
        return job
    finally:
        if work_dir.exists():
            shutil.rmtree(work_dir, ignore_errors=True)


async def get_latest_completed_index_job(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    revision_id: UUID,
) -> GitHubIndexJobORM | None:
    return await session.scalar(
        select(GitHubIndexJobORM)
        .where(
            GitHubIndexJobORM.workspace_id == workspace_id,
            GitHubIndexJobORM.revision_id == revision_id,
            GitHubIndexJobORM.status == GitHubIndexJobStatus.completed,
        )
        .order_by(GitHubIndexJobORM.created_at.desc())
        .limit(1)
    )


async def get_latest_index_job(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    revision_id: UUID,
) -> GitHubIndexJobORM | None:
    return await session.scalar(
        select(GitHubIndexJobORM)
        .where(
            GitHubIndexJobORM.workspace_id == workspace_id,
            GitHubIndexJobORM.revision_id == revision_id,
        )
        .order_by(GitHubIndexJobORM.created_at.desc())
        .limit(1)
    )


async def list_revision_chunks(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    repository_id: UUID,
    pull_request_id: UUID,
    revision_id: UUID,
    limit: int = CHUNK_LIST_DEFAULT_LIMIT,
    offset: int = 0,
) -> GitHubCodeChunkListResponse:
    await ensure_revision_access(
        session,
        workspace_id=workspace_id,
        repository_id=repository_id,
        pull_request_id=pull_request_id,
        revision_id=revision_id,
    )

    rows = list(
        await session.scalars(
            select(GitHubCodeChunkORM)
            .where(
                GitHubCodeChunkORM.workspace_id == workspace_id,
                GitHubCodeChunkORM.revision_id == revision_id,
            )
            .order_by(GitHubCodeChunkORM.file_path, GitHubCodeChunkORM.chunk_index)
            .offset(offset)
            .limit(limit + 1)
        )
    )
    has_more = len(rows) > limit
    if has_more:
        rows = rows[:limit]

    return GitHubCodeChunkListResponse(
        items=[GitHubCodeChunkResponse.model_validate(row) for row in rows],
        offset=offset,
        limit=limit,
        has_more=has_more,
    )


async def search_revision_chunks(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    repository_id: UUID,
    pull_request_id: UUID,
    revision_id: UUID,
    query: str,
    top_k: int,
    file_paths: frozenset[str] | None = None,
) -> list[GitHubChunkSearchResult]:
    if not settings.embeddings_enabled:
        raise ServiceUnavailableError(
            message="Embeddings API is not configured",
            error_code="embeddings_disabled",
        )

    await ensure_revision_access(
        session,
        workspace_id=workspace_id,
        repository_id=repository_id,
        pull_request_id=pull_request_id,
        revision_id=revision_id,
    )

    async with httpx.AsyncClient(timeout=60.0) as client:
        query_embedding = await embed_query(client, query)

    distance_expr = GitHubCodeChunkORM.embedding.cosine_distance(query_embedding)
    filters = [
        GitHubCodeChunkORM.workspace_id == workspace_id,
        GitHubCodeChunkORM.revision_id == revision_id,
        GitHubCodeChunkORM.embedding.is_not(None),
    ]
    if file_paths is not None:
        if not file_paths:
            return []
        filters.append(GitHubCodeChunkORM.file_path.in_(file_paths))
    result = await session.execute(
        select(GitHubCodeChunkORM, distance_expr.label("distance"))
        .where(*filters)
        .order_by(distance_expr)
        .limit(top_k)
    )

    results: list[GitHubChunkSearchResult] = []
    for row, dist in result.all():
        results.append(
            GitHubChunkSearchResult(
                id=row.id,
                file_path=row.file_path,
                chunk_index=row.chunk_index,
                content=row.content,
                score=1.0 - float(dist),
            )
        )
    return results
