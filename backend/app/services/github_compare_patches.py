# backend/app/services/github_compare_patches.py
"""GitHub compare patches — shared helper for judge and resolution metrics."""
from __future__ import annotations

from dataclasses import dataclass

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, RateLimitedError, ServiceUnavailableError
from app.core.logging import get_logger
from app.integrations.github_api import compare_commits
from app.models.github_installation import GitHubInstallationORM
from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
from app.models.github_repository import GitHubRepositoryORM

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class ComparePatchesResult:
    patches_by_file: dict[str, str]
    compare_failed: bool


async def fetch_compare_patches(
    session: AsyncSession,
    *,
    pull_request: GitHubPullRequestORM,
    base_sha: str | None,
    head_sha: str | None,
    log_event: str = "compare_patches_failed",
    skip_when_same_sha: bool = True,
) -> ComparePatchesResult:
    """Load per-file patches for a base/head SHA pair."""
    if not base_sha or not head_sha:
        return ComparePatchesResult({}, False)
    if skip_when_same_sha and base_sha == head_sha:
        return ComparePatchesResult({}, False)

    repository = await session.get(GitHubRepositoryORM, pull_request.repository_id)
    installation = await session.get(GitHubInstallationORM, pull_request.installation_id)
    if repository is None or installation is None:
        return ComparePatchesResult({}, False)

    owner, repo_name = repository.full_name.split("/", 1)
    async with httpx.AsyncClient(timeout=120.0) as client:
        try:
            compare = await compare_commits(
                client,
                github_installation_id=installation.github_installation_id,
                owner=owner,
                repo=repo_name,
                base_sha=base_sha,
                head_sha=head_sha,
            )
        except (httpx.HTTPError, OSError, NotFoundError, RateLimitedError, ServiceUnavailableError) as exc:
            logger.warning(
                log_event,
                extra={
                    "pull_request_id": str(pull_request.id),
                    "base_sha": base_sha,
                    "head_sha": head_sha,
                    "error": str(exc),
                },
            )
            return ComparePatchesResult({}, True)

    patches = {item.filename: item.patch for item in compare.files if item.patch}
    return ComparePatchesResult(patches, False)


async def fetch_compare_patches_by_file(
    session: AsyncSession,
    *,
    pull_request: GitHubPullRequestORM,
    revision: GitHubPullRequestRevisionORM,
) -> dict[str, str]:
    """Load per-file patches for a revision (same base/head pair as review ingest)."""
    result = await fetch_compare_patches(
        session,
        pull_request=pull_request,
        base_sha=revision.base_sha,
        head_sha=revision.head_sha,
        log_event="judge_compare_patches_failed",
        skip_when_same_sha=False,
    )
    return result.patches_by_file
