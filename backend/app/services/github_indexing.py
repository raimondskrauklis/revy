# backend/app/services/github_indexing.py
"""GitHub PR revision indexing — R3."""
from __future__ import annotations

import shutil
from pathlib import Path
from uuid import UUID

import httpx
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import GitHubIndexJobStatus
from app.core.config import settings
from app.core.exceptions import NotFoundError, ServiceUnavailableError
from app.core.logging import get_logger
from app.integrations.github_archive import (
    download_repository_tarball,
    extract_tarball,
    iter_indexable_files,
)
from app.integrations.voyage_embeddings import embed_query, embed_texts
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

    job = GitHubIndexJobORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubIndexJobStatus.pending,
    )
    session.add(job)
    await session.flush()
    return job


def enqueue_index_job(index_job_id: UUID) -> None:
    from app.workers.index_tasks import index_pull_request_revision

    index_pull_request_revision.delay(str(index_job_id))


async def run_index_job(session: AsyncSession, *, index_job_id: UUID) -> GitHubIndexJobORM:
    job = await session.get(GitHubIndexJobORM, index_job_id)
    if job is None:
        raise NotFoundError("Index job not found")

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
        async with httpx.AsyncClient(timeout=120.0) as client:
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

        raw_chunks: list[tuple[str, int, str]] = []
        for file_path, content in iter_indexable_files(root_dir):
            for chunk in chunk_file_content(file_path, content):
                raw_chunks.append((chunk.file_path, chunk.chunk_index, chunk.content))

        if not raw_chunks:
            await session.execute(
                delete(GitHubCodeChunkORM).where(GitHubCodeChunkORM.revision_id == job.revision_id)
            )
            job.status = GitHubIndexJobStatus.completed
            job.chunk_count = 0
            await session.flush()
            return job

        texts = [item[2] for item in raw_chunks]
        async with httpx.AsyncClient(timeout=120.0) as client:
            embeddings = await embed_texts(client, texts)

        if len(embeddings) != len(raw_chunks):
            raise RuntimeError("embedding_count_mismatch")

        await session.execute(
            delete(GitHubCodeChunkORM).where(GitHubCodeChunkORM.revision_id == job.revision_id)
        )

        for (file_path, chunk_index, content), embedding in zip(raw_chunks, embeddings, strict=True):
            session.add(
                GitHubCodeChunkORM(
                    index_job_id=job.id,
                    revision_id=job.revision_id,
                    workspace_id=job.workspace_id,
                    file_path=file_path,
                    chunk_index=chunk_index,
                    content=content,
                    embedding=embedding,
                )
            )

        job.status = GitHubIndexJobStatus.completed
        job.chunk_count = len(raw_chunks)
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
    result = await session.execute(
        select(GitHubCodeChunkORM, distance_expr.label("distance"))
        .where(
            GitHubCodeChunkORM.workspace_id == workspace_id,
            GitHubCodeChunkORM.revision_id == revision_id,
            GitHubCodeChunkORM.embedding.is_not(None),
        )
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
