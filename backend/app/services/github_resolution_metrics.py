# backend/app/services/github_resolution_metrics.py
"""Resolution metrics on synchronize — RQ6 (M2)."""
from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import GitHubFindingGroupState, ResolutionStatus
from app.models.github_finding import GitHubFindingORM
from app.models.github_finding_group import GitHubFindingGroupORM
from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
from app.services.github_compare_patches import ComparePatchesResult, fetch_compare_patches
from app.services.github_finding_closure import COMPARE_FAILED_REASON

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
) -> ComparePatchesResult:
    return await fetch_compare_patches(
        session,
        pull_request=pull_request,
        base_sha=prior_revision.head_sha,
        head_sha=new_revision.head_sha,
        log_event="resolution_metrics_compare_failed",
    )


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

    compare_result = await _fetch_compare_patches(
        session,
        pull_request=pull_request,
        prior_revision=prior_revision,
        new_revision=new_revision,
    )

    updated = 0
    for group in groups:
        if compare_result.compare_failed:
            group.closure_blocked_reason = COMPARE_FAILED_REASON
            group.resolution_status = ResolutionStatus.still_open
            updated += 1
            continue

        group.closure_blocked_reason = None
        start_line, end_line = await _latest_finding_lines(session, group_id=group.id)
        group.resolution_status = resolve_group_resolution_status(
            group=group,
            patches_by_file=compare_result.patches_by_file,
            start_line=start_line,
            end_line=end_line,
        )
        updated += 1

    await session.flush()
    return updated
