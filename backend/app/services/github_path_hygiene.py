# backend/app/services/github_path_hygiene.py
"""HEAD-truth path hygiene — CS-Q7 path absent at revision head_sha."""
from __future__ import annotations

import httpx
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, RateLimitedError, ServiceUnavailableError
from app.integrations.github_api import fetch_repository_file_at_sha
from app.models.github_installation import GitHubInstallationORM
from app.models.github_pull_request import GitHubPullRequestORM
from app.models.github_repository import GitHubRepositoryORM


async def path_absent_at_head(
    client: httpx.AsyncClient,
    *,
    github_installation_id: int,
    owner: str,
    repo: str,
    file_path: str,
    head_sha: str,
) -> bool | None:
    """True when path missing at head_sha; False when present; None on API error."""
    try:
        await fetch_repository_file_at_sha(
            client,
            github_installation_id=github_installation_id,
            owner=owner,
            repo=repo,
            path=file_path,
            ref=head_sha,
        )
    except NotFoundError as exc:
        if exc.error_code == "github_contents_not_found":
            return True
        return None
    except (httpx.HTTPError, OSError, RateLimitedError, ServiceUnavailableError):
        return None
    else:
        return False


def hygiene_path_gone(
    file_path: str,
    *,
    absent_at_head: bool | None,
    renamed_from_paths: frozenset[str],
) -> bool | None:
    """Whether Pass 1b should stamp addressed for path-gone hygiene."""
    if file_path in renamed_from_paths:
        return False
    return absent_at_head


async def paths_absent_at_head(
    session: AsyncSession,
    *,
    pull_request: GitHubPullRequestORM,
    head_sha: str,
    file_paths: frozenset[str],
    client: httpx.AsyncClient | None = None,
) -> dict[str, bool | None]:
    """Batch HEAD existence check for unique file paths."""
    if not file_paths or not head_sha:
        return {}

    repository = await session.get(GitHubRepositoryORM, pull_request.repository_id)
    installation = await session.get(GitHubInstallationORM, pull_request.installation_id)
    if repository is None or installation is None:
        return dict.fromkeys(file_paths, None)

    if "/" not in repository.full_name:
        return dict.fromkeys(file_paths, None)

    owner, repo_name = repository.full_name.split("/", 1)
    if not owner or not repo_name:
        return dict.fromkeys(file_paths, None)
    github_installation_id = installation.github_installation_id

    async def _check_paths(http_client: httpx.AsyncClient) -> dict[str, bool | None]:
        results: dict[str, bool | None] = {}
        for file_path in sorted(file_paths):
            results[file_path] = await path_absent_at_head(
                http_client,
                github_installation_id=github_installation_id,
                owner=owner,
                repo=repo_name,
                file_path=file_path,
                head_sha=head_sha,
            )
        return results

    if client is not None:
        return await _check_paths(client)

    async with httpx.AsyncClient(timeout=60.0) as http_client:
        return await _check_paths(http_client)
