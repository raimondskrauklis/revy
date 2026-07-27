# backend/app/services/github_resolution_metrics.py
"""Resolution metrics on synchronize — RQ6 (M2)."""
from __future__ import annotations

import re
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import GitHubFindingGroupState, ResolutionStatus
from app.core.exceptions import NotFoundError, RateLimitedError, ServiceUnavailableError
from app.core.logging import get_logger
from app.integrations.github_api import compare_commits
from app.models.github_finding import GitHubFindingORM
from app.models.github_finding_group import GitHubFindingGroupORM
from app.models.github_installation import GitHubInstallationORM
from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
from app.models.github_repository import GitHubRepositoryORM

logger = get_logger(__name__)

_HUNK_HEADER_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def patch_touches_line_region(
    patch: str,
    *,
    start_line: int | None,
    end_line: int | None,
) -> bool:
    """True when the unified diff patch modifies lines overlapping the finding region."""
    if not patch.strip():
        return False
    if start_line is None:
        return any(line.startswith(("+", "-")) and not line.startswith(("+++", "---")) for line in patch.splitlines())

    region_end = end_line if end_line is not None else start_line
    region = set(range(start_line, region_end + 1))
    new_line = 0
    modified_lines: set[int] = set()

    for line in patch.splitlines():
        hunk_match = _HUNK_HEADER_RE.match(line)
        if hunk_match is not None:
            new_line = int(hunk_match.group(1)) - 1
            continue
        if line.startswith("+++") or line.startswith("---") or line.startswith("\\"):
            continue
        if line.startswith("+"):
            new_line += 1
            modified_lines.add(new_line)
        elif line.startswith("-"):
            modified_lines.add(max(new_line, 1))
        elif line.startswith(" "):
            new_line += 1

    return bool(region & modified_lines)


async def _fetch_compare_patches(
    session: AsyncSession,
    *,
    pull_request: GitHubPullRequestORM,
    prior_revision: GitHubPullRequestRevisionORM,
    new_revision: GitHubPullRequestRevisionORM,
) -> dict[str, str]:
    base_sha = prior_revision.head_sha
    head_sha = new_revision.head_sha
    if not base_sha or not head_sha or base_sha == head_sha:
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
                "resolution_metrics_compare_failed",
                extra={"pull_request_id": str(pull_request.id), "error": str(exc)},
            )
            return {}

    return {item.filename: item.patch for item in compare.files if item.patch}


async def _latest_finding_lines(
    session: AsyncSession,
    *,
    group_id: UUID,
) -> tuple[int | None, int | None]:
    finding = await session.scalar(
        select(GitHubFindingORM)
        .where(GitHubFindingORM.group_id == group_id)
        .order_by(GitHubFindingORM.created_at.desc())
        .limit(1)
    )
    if finding is None:
        return None, None
    return finding.start_line, finding.end_line


def resolve_group_resolution_status(
    *,
    group: GitHubFindingGroupORM,
    patches_by_file: dict[str, str],
    start_line: int | None,
    end_line: int | None,
) -> ResolutionStatus:
    if group.state == GitHubFindingGroupState.resolved:
        return ResolutionStatus.judge_dismissed

    file_path = group.file_path
    if not file_path:
        return ResolutionStatus.still_open

    patch = patches_by_file.get(file_path)
    if patch is None:
        return ResolutionStatus.still_open

    if patch_touches_line_region(patch, start_line=start_line, end_line=end_line):
        return ResolutionStatus.addressed
    return ResolutionStatus.still_open


async def apply_resolution_status_for_synchronize(
    session: AsyncSession,
    *,
    pull_request: GitHubPullRequestORM,
    new_revision: GitHubPullRequestRevisionORM,
) -> int:
    """Stamp resolution_status on prior-revision groups before the next pipeline run."""
    prior_revision = await session.scalar(
        select(GitHubPullRequestRevisionORM).where(
            GitHubPullRequestRevisionORM.pull_request_id == pull_request.id,
            GitHubPullRequestRevisionORM.revision_number == new_revision.revision_number - 1,
        )
    )
    if prior_revision is None:
        return 0

    stale_groups = list(
        await session.scalars(
            select(GitHubFindingGroupORM).where(
                GitHubFindingGroupORM.pull_request_id == pull_request.id,
                GitHubFindingGroupORM.state != GitHubFindingGroupState.superseded,
            )
        )
    )
    for group in stale_groups:
        group.resolution_status = None

    groups = [
        group
        for group in stale_groups
        if group.last_seen_revision_id == prior_revision.id
    ]
    if not groups:
        await session.flush()
        return 0

    patches_by_file = await _fetch_compare_patches(
        session,
        pull_request=pull_request,
        prior_revision=prior_revision,
        new_revision=new_revision,
    )

    updated = 0
    for group in groups:
        start_line, end_line = await _latest_finding_lines(session, group_id=group.id)
        group.resolution_status = resolve_group_resolution_status(
            group=group,
            patches_by_file=patches_by_file,
            start_line=start_line,
            end_line=end_line,
        )
        updated += 1

    await session.flush()
    return updated
