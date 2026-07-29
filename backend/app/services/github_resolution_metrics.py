# backend/app/services/github_resolution_metrics.py
"""Resolution metrics on synchronize — RQ6 (M2)."""
from __future__ import annotations

import re
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import (
    GitHubFindingGroupState,
    GitHubPublishJobStatus,
    ResolutionMethod,
    ResolutionStatus,
)
from app.models.github_finding import GitHubFindingORM
from app.models.github_finding_group import GitHubFindingGroupORM
from app.models.github_publish_job import GitHubPublishJobORM
from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
from app.models.github_review_run import GitHubReviewRunORM
from app.services.github_compare_patches import ComparePatchesResult, fetch_compare_patches
from app.services.github_finding_closure_rules import (
    COMPARE_FAILED_REASON,
    HEAD_CHECK_FAILED_REASON,
)
from app.services.github_path_hygiene import hygiene_path_gone, paths_absent_at_head

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


def file_path_removed_in_compare(
    file_path: str,
    *,
    removed_paths: frozenset[str],
) -> bool:
    """True when GitHub compare removed the group's file between prior and current head."""
    return file_path in removed_paths


def resolve_group_resolution_status(
    *,
    group: GitHubFindingGroupORM,
    patches_by_file: dict[str, str],
    removed_paths: frozenset[str],
    start_line: int | None,
    end_line: int | None,
) -> ResolutionStatus:
    if group.state == GitHubFindingGroupState.resolved:
        return ResolutionStatus.judge_dismissed

    file_path = group.file_path
    if not file_path:
        return ResolutionStatus.still_open

    if file_path_removed_in_compare(file_path, removed_paths=removed_paths):
        return ResolutionStatus.addressed

    patch = patches_by_file.get(file_path)
    if patch is None:
        return ResolutionStatus.still_open

    if patch_touches_line_region(patch, start_line=start_line, end_line=end_line):
        return ResolutionStatus.addressed
    return ResolutionStatus.still_open


async def get_intermediate_revision_ids_between(
    session: AsyncSession,
    *,
    pull_request_id: UUID,
    prior_revision: GitHubPullRequestRevisionORM,
    current_revision: GitHubPullRequestRevisionORM,
) -> frozenset[UUID]:
    """Revisions after last published prior and before current (unpublished gap)."""
    if current_revision.revision_number <= prior_revision.revision_number + 1:
        return frozenset()
    rows = await session.scalars(
        select(GitHubPullRequestRevisionORM.id).where(
            GitHubPullRequestRevisionORM.pull_request_id == pull_request_id,
            GitHubPullRequestRevisionORM.revision_number > prior_revision.revision_number,
            GitHubPullRequestRevisionORM.revision_number < current_revision.revision_number,
        )
    )
    return frozenset(rows)


def prior_publish_pairing_revision_ids(
    *,
    prior_revision: GitHubPullRequestRevisionORM,
    intermediate_revision_ids: frozenset[UUID],
) -> frozenset[UUID]:
    return frozenset({prior_revision.id, *intermediate_revision_ids})


async def get_last_published_prior_revision(
    session: AsyncSession,
    *,
    pull_request_id: UUID,
    current_revision: GitHubPullRequestRevisionORM,
) -> GitHubPullRequestRevisionORM | None:
    """Walk back to the latest prior revision with a completed publish job."""
    return await session.scalar(
        select(GitHubPullRequestRevisionORM)
        .join(
            GitHubReviewRunORM,
            GitHubReviewRunORM.revision_id == GitHubPullRequestRevisionORM.id,
        )
        .join(
            GitHubPublishJobORM,
            GitHubPublishJobORM.review_run_id == GitHubReviewRunORM.id,
        )
        .where(
            GitHubPullRequestRevisionORM.pull_request_id == pull_request_id,
            GitHubPullRequestRevisionORM.revision_number < current_revision.revision_number,
            GitHubPublishJobORM.status == GitHubPublishJobStatus.completed,
        )
        .order_by(GitHubPullRequestRevisionORM.revision_number.desc())
        .limit(1)
    )


async def apply_resolution_status_for_synchronize(
    session: AsyncSession,
    *,
    pull_request: GitHubPullRequestORM,
    new_revision: GitHubPullRequestRevisionORM,
) -> int:
    """Stamp resolution_status on prior-revision groups before the next pipeline run."""
    prior_revision = await get_last_published_prior_revision(
        session,
        pull_request_id=pull_request.id,
        current_revision=new_revision,
    )
    if prior_revision is None:
        return 0

    intermediate_revision_ids = await get_intermediate_revision_ids_between(
        session,
        pull_request_id=pull_request.id,
        prior_revision=prior_revision,
        current_revision=new_revision,
    )
    pairing_revision_ids = prior_publish_pairing_revision_ids(
        prior_revision=prior_revision,
        intermediate_revision_ids=intermediate_revision_ids,
    )

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

    cohort_groups = [
        group
        for group in stale_groups
        if group.last_seen_revision_id in pairing_revision_ids
    ]
    active_groups = [
        group
        for group in stale_groups
        if group.state == GitHubFindingGroupState.active and group.file_path
    ]

    compare_result = await _fetch_compare_patches(
        session,
        pull_request=pull_request,
        prior_revision=prior_revision,
        new_revision=new_revision,
    )

    file_paths = frozenset(group.file_path for group in active_groups if group.file_path)
    absent_by_path = await paths_absent_at_head(
        session,
        pull_request=pull_request,
        head_sha=new_revision.head_sha,
        file_paths=file_paths,
    )

    updated = 0

    for group in cohort_groups:
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
            removed_paths=compare_result.removed_paths,
            start_line=start_line,
            end_line=end_line,
        )
        updated += 1

    for group in active_groups:
        file_path = group.file_path
        if not file_path:
            continue

        absent = absent_by_path.get(file_path)

        if compare_result.compare_failed:
            if absent is None and group.resolution_status != ResolutionStatus.addressed:
                if group.closure_blocked_reason != COMPARE_FAILED_REASON:
                    group.closure_blocked_reason = HEAD_CHECK_FAILED_REASON
                    group.resolution_status = ResolutionStatus.still_open
                    updated += 1
            elif (
                absent is False
                and group.closure_blocked_reason == HEAD_CHECK_FAILED_REASON
            ):
                group.closure_blocked_reason = None
            continue

        path_gone = hygiene_path_gone(
            file_path,
            absent_at_head=absent,
            renamed_from_paths=compare_result.renamed_from_paths,
        )
        if path_gone is None:
            if group.resolution_status != ResolutionStatus.addressed:
                group.closure_blocked_reason = HEAD_CHECK_FAILED_REASON
                group.resolution_status = ResolutionStatus.still_open
                updated += 1
            continue
        if not path_gone:
            if group.closure_blocked_reason == HEAD_CHECK_FAILED_REASON:
                group.closure_blocked_reason = None
            continue

        group.closure_blocked_reason = None
        group.resolution_status = ResolutionStatus.addressed
        updated += 1

    await session.flush()
    return updated


def _is_pre_sync_resolved(
    group: GitHubFindingGroupORM,
    *,
    current_revision_id: UUID,
) -> bool:
    return (
        group.state == GitHubFindingGroupState.resolved
        and group.resolved_at_revision_id is not None
        and group.resolved_at_revision_id != current_revision_id
    )


def _in_sync_stamp_cohort(
    group: GitHubFindingGroupORM,
    *,
    prior_revision_ids: frozenset[UUID],
    current_revision_id: UUID,
) -> bool:
    """Groups active on last-published prior (or unpublished gap), including re-reports."""
    if group.last_seen_revision_id in prior_revision_ids:
        return True
    if group.resolved_at_revision_id == current_revision_id:
        return True
    return (
        group.last_seen_revision_id == current_revision_id
        and group.resolution_status is not None
    )


def _is_hygiene_path_removed_closure(
    group: GitHubFindingGroupORM,
    *,
    prior_revision_ids: frozenset[UUID],
    current_revision_id: UUID,
) -> bool:
    return (
        group.state == GitHubFindingGroupState.resolved
        and group.resolution_method == ResolutionMethod.absent_and_addressed
        and group.resolved_at_revision_id == current_revision_id
        and group.last_seen_revision_id not in prior_revision_ids
    )


def build_resolution_pass_manifest(
    groups: list[GitHubFindingGroupORM],
    *,
    prior_revision_ids: frozenset[UUID],
    current_revision_id: UUID,
) -> dict[str, object]:
    """FR-Q12 transitions-only metrics for reconcile manifest resolution_pass."""
    cohort = [
        group
        for group in groups
        if group.state != GitHubFindingGroupState.superseded
        and _in_sync_stamp_cohort(
            group,
            prior_revision_ids=prior_revision_ids,
            current_revision_id=current_revision_id,
        )
    ]
    compare_failed_count = sum(
        1 for group in cohort if group.closure_blocked_reason == COMPARE_FAILED_REASON
    )
    head_check_failed_count = sum(
        1
        for group in groups
        if group.state != GitHubFindingGroupState.superseded
        and group.closure_blocked_reason == HEAD_CHECK_FAILED_REASON
    )
    denominator_groups = [
        group
        for group in cohort
        if group.closure_blocked_reason not in (COMPARE_FAILED_REASON, HEAD_CHECK_FAILED_REASON)
        and not _is_pre_sync_resolved(group, current_revision_id=current_revision_id)
        and not _is_hygiene_path_removed_closure(
            group,
            prior_revision_ids=prior_revision_ids,
            current_revision_id=current_revision_id,
        )
    ]
    transitions = [
        group
        for group in cohort
        if group.state == GitHubFindingGroupState.resolved
        and group.resolved_at_revision_id == current_revision_id
        and group.resolution_method is not None
    ]
    hygiene_path_removed_count = sum(
        1
        for group in transitions
        if _is_hygiene_path_removed_closure(
            group,
            prior_revision_ids=prior_revision_ids,
            current_revision_id=current_revision_id,
        )
    )
    rate_transitions = [
        group
        for group in transitions
        if not _is_hygiene_path_removed_closure(
            group,
            prior_revision_ids=prior_revision_ids,
            current_revision_id=current_revision_id,
        )
    ]
    transitions_addressed = sum(
        1
        for group in rate_transitions
        if group.resolution_method == ResolutionMethod.absent_and_addressed
    )
    transitions_dismissed = {
        ResolutionMethod.judge_dismissed.value: sum(
            1
            for group in rate_transitions
            if group.resolution_method == ResolutionMethod.judge_dismissed
        ),
        ResolutionMethod.verification_dismissed.value: sum(
            1
            for group in rate_transitions
            if group.resolution_method == ResolutionMethod.verification_dismissed
        ),
        ResolutionMethod.human_dismissed.value: sum(
            1
            for group in rate_transitions
            if group.resolution_method == ResolutionMethod.human_dismissed
        ),
    }
    transition_count = len(rate_transitions)
    denominator = len(denominator_groups)
    resolution_rate_pct = (
        round(100.0 * transition_count / denominator, 1) if denominator else 0.0
    )
    still_open_count = sum(
        1
        for group in denominator_groups
        if group.state == GitHubFindingGroupState.active
        and group.resolution_status == ResolutionStatus.still_open
    )
    return {
        "transitions_addressed": transitions_addressed,
        "transitions_dismissed": transitions_dismissed,
        "transition_count": transition_count,
        "denominator_active_prior": denominator,
        "resolution_rate_pct": resolution_rate_pct,
        "compare_failed_count": compare_failed_count,
        "head_check_failed_count": head_check_failed_count,
        "hygiene_path_removed_count": hygiene_path_removed_count,
        "still_open_count": still_open_count,
    }


async def compute_resolution_transitions(
    session: AsyncSession,
    *,
    pull_request: GitHubPullRequestORM,
    prior_revision: GitHubPullRequestRevisionORM,
    current_revision: GitHubPullRequestRevisionORM,
) -> dict[str, object]:
    groups = list(
        await session.scalars(
            select(GitHubFindingGroupORM).where(
                GitHubFindingGroupORM.pull_request_id == pull_request.id,
                GitHubFindingGroupORM.state != GitHubFindingGroupState.superseded,
            )
        )
    )
    intermediate_revision_ids = await get_intermediate_revision_ids_between(
        session,
        pull_request_id=pull_request.id,
        prior_revision=prior_revision,
        current_revision=current_revision,
    )
    return build_resolution_pass_manifest(
        groups,
        prior_revision_ids=prior_publish_pairing_revision_ids(
            prior_revision=prior_revision,
            intermediate_revision_ids=intermediate_revision_ids,
        ),
        current_revision_id=current_revision.id,
    )
