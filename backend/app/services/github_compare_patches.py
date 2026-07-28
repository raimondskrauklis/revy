# backend/app/services/github_compare_patches.py
"""GitHub compare patches for judge scoped context — J-8."""
from __future__ import annotations

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, RateLimitedError, ServiceUnavailableError
from app.core.logging import get_logger
from app.integrations.github_api import compare_commits
from app.models.github_installation import GitHubInstallationORM
from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
from app.models.github_repository import GitHubRepositoryORM

logger = get_logger(__name__)


async def fetch_compare_patches_by_file(
    session: AsyncSession,
    *,
    pull_request: GitHubPullRequestORM,
    revision: GitHubPullRequestRevisionORM,
) -> dict[str, str]:
    """Load per-file patches for a revision (same base/head pair as review ingest)."""
    base_sha = revision.base_sha
    head_sha = revision.head_sha
    if not base_sha or not head_sha:
        return {}

    repository = await session.get(GitHubRepositoryORM, pull_request.repository_id)
    installation = await session.get(GitHubInstallationORM, pull_request.installation_id)
    if repository is None or installation is None:
        return {}

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
                "judge_compare_patches_failed",
                extra={
                    "pull_request_id": str(pull_request.id),
                    "revision_id": str(revision.id),
                    "error": str(exc),
                },
            )
            return {}

    return {item.filename: item.patch for item in compare.files if item.patch}
