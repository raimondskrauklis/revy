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
from app.core.logging import get_logger
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
from app.services.github_publish import deserialize_inline_thread_map

logger = get_logger(__name__)

_HUNK_HEADER_RE = re.compile(r"^@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@")


def patch_touches_line_region(
    patch: str,
    *,
    start_line: int | None,
    end_line: int | None,
) -> bool:
    """True when the unified diff patch modifies lines overlapping the finding region.

    Finding ``start_line`` is on the last-seen file (old side of the next
    compare). Deletions must count old-file line numbers, not only the new side.
    """
    if not patch.strip():
        return False
    if start_line is None:
        return any(
            line.startswith(("+", "-")) and not line.startswith(("+++", "---"))
            for line in patch.splitlines()
        )

    region_end = end_line if end_line is not None else start_line
    region = set(range(start_line, region_end + 1))
    old_line = 0
    new_line = 0
    modified_lines: set[int] = set()

    for line in patch.splitlines():
        hunk_match = _HUNK_HEADER_RE.match(line)
        if hunk_match is not None:
            old_line = int(hunk_match.group(1)) - 1
            new_line = int(hunk_match.group(2)) - 1
            continue
        if line.startswith("+++") or line.startswith("---") or line.startswith("\\"):
            continue
        if line.startswith("+"):
            new_line += 1
            modified_lines.add(new_line)
        elif line.startswith("-"):
            old_line += 1
            modified_lines.add(old_line)
        elif line.startswith(" "):
            old_line += 1
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
    lines_by_group = await _latest_finding_lines_by_group_ids(session, frozenset({group_id}))
    return lines_by_group.get(group_id, (None, None))


async def _latest_finding_lines_by_group_ids(
    session: AsyncSession,
    group_ids: frozenset[UUID],
) -> dict[UUID, tuple[int | None, int | None]]:
    if not group_ids:
        return {}
    rows = await session.execute(
        select(
            GitHubFindingORM.group_id,
            GitHubFindingORM.start_line,
            GitHubFindingORM.end_line,
            GitHubFindingORM.created_at,
        )
        .where(
            GitHubFindingORM.group_id.in_(group_ids),
            GitHubFindingORM.group_id.is_not(None),
        )
        .order_by(GitHubFindingORM.group_id, GitHubFindingORM.created_at.desc())
    )
    lines_by_group: dict[UUID, tuple[int | None, int | None]] = {}
    for group_id, start_line, end_line, _created_at in rows:
        if group_id is None or group_id in lines_by_group:
            continue
        lines_by_group[group_id] = (start_line, end_line)
    return lines_by_group


def file_path_deleted_in_compare(
    file_path: str,
    *,
    deleted_paths: frozenset[str],
) -> bool:
    """True when GitHub compare deleted the group's file between prior and current head."""
    return file_path in deleted_paths


def resolve_group_resolution_status(
    *,
    group: GitHubFindingGroupORM,
    patches_by_file: dict[str, str],
    deleted_paths: frozenset[str],
    start_line: int | None,
    end_line: int | None,
) -> ResolutionStatus:
    if group.state == GitHubFindingGroupState.resolved:
        return ResolutionStatus.judge_dismissed

    file_path = group.file_path
    if not file_path:
        return ResolutionStatus.still_open

    if file_path_deleted_in_compare(file_path, deleted_paths=deleted_paths):
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


async def _revisions_with_completed_publish(
    session: AsyncSession,
    revision_ids: frozenset[UUID],
) -> frozenset[UUID]:
    if not revision_ids:
        return frozenset()
    rows = await session.scalars(
        select(GitHubReviewRunORM.revision_id)
        .join(
            GitHubPublishJobORM,
            GitHubPublishJobORM.review_run_id == GitHubReviewRunORM.id,
        )
        .where(
            GitHubReviewRunORM.revision_id.in_(revision_ids),
            GitHubPublishJobORM.status == GitHubPublishJobStatus.completed,
        )
        .distinct()
    )
    return frozenset(rows)


async def _published_revisions_for_pull_request(
    session: AsyncSession,
    *,
    pull_request_id: UUID,
) -> list[GitHubPullRequestRevisionORM]:
    return list(
        await session.scalars(
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
                GitHubPublishJobORM.status == GitHubPublishJobStatus.completed,
            )
            .order_by(GitHubPullRequestRevisionORM.revision_number.asc())
            .distinct()
        )
    )


async def resolve_pairing_last_seen_revision_ids(
    session: AsyncSession,
    *,
    pull_request_id: UUID,
    last_seen_revision_ids: frozenset[UUID],
) -> dict[UUID, UUID]:
    if not last_seen_revision_ids:
        return {}

    targets = {
        row.id: row
        for row in await session.scalars(
            select(GitHubPullRequestRevisionORM).where(
                GitHubPullRequestRevisionORM.id.in_(last_seen_revision_ids),
            )
        )
    }
    published_ids = await _revisions_with_completed_publish(session, last_seen_revision_ids)
    published_revisions = await _published_revisions_for_pull_request(
        session,
        pull_request_id=pull_request_id,
    )
    published_by_number = [
        (revision.id, revision.revision_number) for revision in published_revisions
    ]

    resolved: dict[UUID, UUID] = {}
    for last_seen_id in last_seen_revision_ids:
        target = targets.get(last_seen_id)
        if target is None or target.pull_request_id != pull_request_id:
            resolved[last_seen_id] = last_seen_id
            continue
        if last_seen_id in published_ids:
            resolved[last_seen_id] = last_seen_id
            continue
        prior_id = last_seen_id
        for published_id, published_number in reversed(published_by_number):
            if published_number < target.revision_number:
                prior_id = published_id
                break
        resolved[last_seen_id] = prior_id
    return resolved


async def resolve_pairing_last_seen_revision_id(
    session: AsyncSession,
    *,
    pull_request_id: UUID,
    last_seen_revision_id: UUID,
) -> UUID:
    """R3.3 — map last_seen on an unpublished revision to nearest prior published revision."""
    resolved = await resolve_pairing_last_seen_revision_ids(
        session,
        pull_request_id=pull_request_id,
        last_seen_revision_ids=frozenset({last_seen_revision_id}),
    )
    return resolved.get(last_seen_revision_id, last_seen_revision_id)


async def _fingerprints_by_review_run_ids(
    session: AsyncSession,
    review_run_ids: frozenset[UUID],
) -> dict[UUID, frozenset[str]]:
    if not review_run_ids:
        return {}
    rows = await session.execute(
        select(GitHubFindingORM.review_run_id, GitHubFindingGroupORM.fingerprint)
        .join(
            GitHubFindingGroupORM,
            GitHubFindingGroupORM.id == GitHubFindingORM.group_id,
        )
        .where(
            GitHubFindingORM.review_run_id.in_(review_run_ids),
            GitHubFindingORM.group_id.is_not(None),
        )
    )
    grouped: dict[UUID, set[str]] = {}
    for review_run_id, fingerprint in rows:
        if review_run_id is None or not isinstance(fingerprint, str) or not fingerprint:
            continue
        grouped.setdefault(review_run_id, set()).add(fingerprint)
    return {run_id: frozenset(fingerprints) for run_id, fingerprints in grouped.items()}


def _fingerprints_from_publish_summary(summary_json: object) -> frozenset[str]:
    if not isinstance(summary_json, dict):
        return frozenset()
    inline = summary_json.get("github_inline_threads")
    return frozenset(deserialize_inline_thread_map(inline))


async def get_fingerprint_published_revision_ids(
    session: AsyncSession,
    *,
    pull_request_id: UUID,
    current_revision: GitHubPullRequestRevisionORM,
) -> dict[str, UUID]:
    """Latest completed publish revision per fingerprint on this PR up to current."""
    rows = await session.execute(
        select(
            GitHubPublishJobORM.summary_json.label("summary_json"),
            GitHubReviewRunORM.revision_id.label("revision_id"),
            GitHubPublishJobORM.review_run_id.label("review_run_id"),
            GitHubPullRequestRevisionORM.revision_number.label("revision_number"),
        )
        .join(
            GitHubReviewRunORM,
            GitHubReviewRunORM.id == GitHubPublishJobORM.review_run_id,
        )
        .join(
            GitHubPullRequestRevisionORM,
            GitHubPullRequestRevisionORM.id == GitHubReviewRunORM.revision_id,
        )
        .where(
            GitHubPullRequestRevisionORM.pull_request_id == pull_request_id,
            GitHubPullRequestRevisionORM.revision_number <= current_revision.revision_number,
            GitHubPublishJobORM.status == GitHubPublishJobStatus.completed,
        )
        .order_by(
            GitHubPullRequestRevisionORM.revision_number.asc(),
            GitHubPublishJobORM.created_at.asc(),
        )
    )
    row_list = rows.all()
    fingerprints_by_run = await _fingerprints_by_review_run_ids(
        session,
        frozenset(row.review_run_id for row in row_list),
    )
    published: dict[str, UUID] = {}
    for row in row_list:
        fingerprints = set(_fingerprints_from_publish_summary(row.summary_json))
        fingerprints |= set(fingerprints_by_run.get(row.review_run_id, frozenset()))
        for fingerprint in fingerprints:
            published[fingerprint] = row.revision_id
    return published


def _group_in_synchronize_cohort(
    group: GitHubFindingGroupORM,
    *,
    pairing_revision_ids: frozenset[UUID],
    effective_last_seen_revision_id: UUID,
    fingerprint_published_revision_id: UUID | None,
    current_revision_number: int,
    published_revision_numbers: dict[UUID, int],
) -> bool:
    if effective_last_seen_revision_id in pairing_revision_ids:
        return True
    if group.last_seen_revision_id in pairing_revision_ids:
        return True
    if fingerprint_published_revision_id is None:
        return False
    published_number = published_revision_numbers.get(fingerprint_published_revision_id)
    return published_number is not None and published_number <= current_revision_number


async def _build_synchronize_cohort_groups(
    session: AsyncSession,
    *,
    stale_groups: list[GitHubFindingGroupORM],
    pairing_revision_ids: frozenset[UUID],
    pull_request_id: UUID,
    current_revision: GitHubPullRequestRevisionORM,
    fingerprint_published_revision_ids: dict[str, UUID],
    published_revision_numbers: dict[UUID, int],
) -> list[GitHubFindingGroupORM]:
    last_seen_ids_to_resolve = frozenset(
        group.last_seen_revision_id
        for group in stale_groups
        if group.last_seen_revision_id not in pairing_revision_ids
    )
    if last_seen_ids_to_resolve:
        effective_last_seen_by_group = await resolve_pairing_last_seen_revision_ids(
            session,
            pull_request_id=pull_request_id,
            last_seen_revision_ids=last_seen_ids_to_resolve,
        )
    else:
        effective_last_seen_by_group = {}
    cohort: list[GitHubFindingGroupORM] = []
    for group in stale_groups:
        effective_last_seen = effective_last_seen_by_group.get(
            group.last_seen_revision_id,
            group.last_seen_revision_id,
        )
        published_revision_id = fingerprint_published_revision_ids.get(group.fingerprint)
        in_cohort = _group_in_synchronize_cohort(
            group,
            pairing_revision_ids=pairing_revision_ids,
            effective_last_seen_revision_id=effective_last_seen,
            fingerprint_published_revision_id=published_revision_id,
            current_revision_number=current_revision.revision_number,
            published_revision_numbers=published_revision_numbers,
        )
        if not in_cohort:
            continue
        if effective_last_seen != group.last_seen_revision_id or (
            published_revision_id is not None
            and group.last_seen_revision_id not in pairing_revision_ids
            and effective_last_seen not in pairing_revision_ids
        ):
            logger.info(
                "resolution_pairing_repaired",
                extra={
                    "pull_request_id": str(pull_request_id),
                    "fingerprint": group.fingerprint,
                    "last_seen_revision_id": str(group.last_seen_revision_id),
                    "effective_last_seen_revision_id": str(effective_last_seen),
                    "published_revision_id": (
                        str(published_revision_id) if published_revision_id else None
                    ),
                },
            )
        cohort.append(group)
    return cohort


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

    fingerprint_published_revision_ids = await get_fingerprint_published_revision_ids(
        session,
        pull_request_id=pull_request.id,
        current_revision=new_revision,
    )
    published_revision_numbers: dict[UUID, int] = {
        new_revision.id: new_revision.revision_number,
        prior_revision.id: prior_revision.revision_number,
    }
    extra_revision_ids = {
        revision_id
        for revision_id in fingerprint_published_revision_ids.values()
        if revision_id not in published_revision_numbers
    }
    if extra_revision_ids:
        extra_rows = list(
            await session.scalars(
                select(GitHubPullRequestRevisionORM).where(
                    GitHubPullRequestRevisionORM.id.in_(extra_revision_ids),
                )
            )
        )
        published_revision_numbers.update({row.id: row.revision_number for row in extra_rows})

    cohort_groups = await _build_synchronize_cohort_groups(
        session,
        stale_groups=stale_groups,
        pairing_revision_ids=pairing_revision_ids,
        pull_request_id=pull_request.id,
        current_revision=new_revision,
        fingerprint_published_revision_ids=fingerprint_published_revision_ids,
        published_revision_numbers=published_revision_numbers,
    )
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
    compare_fast_path = not compare_result.compare_failed
    absent_by_path = await paths_absent_at_head(
        session,
        pull_request=pull_request,
        head_sha=new_revision.head_sha,
        file_paths=file_paths,
        deleted_paths=compare_result.deleted_paths if compare_fast_path else None,
        renamed_from_paths=compare_result.renamed_from_paths if compare_fast_path else None,
    )

    updated = 0
    updated_group_ids: set[UUID] = set()

    def _count_group_update(group: GitHubFindingGroupORM) -> None:
        nonlocal updated
        if group.id in updated_group_ids:
            return
        updated_group_ids.add(group.id)
        updated += 1

    cohort_group_ids = frozenset(group.id for group in cohort_groups)
    finding_lines_by_group = await _latest_finding_lines_by_group_ids(session, cohort_group_ids)

    for group in cohort_groups:
        if compare_result.compare_failed:
            group.closure_blocked_reason = COMPARE_FAILED_REASON
            group.resolution_status = ResolutionStatus.still_open
            _count_group_update(group)
            continue

        group.closure_blocked_reason = None
        start_line, end_line = finding_lines_by_group.get(group.id, (None, None))
        group.resolution_status = resolve_group_resolution_status(
            group=group,
            patches_by_file=compare_result.patches_by_file,
            deleted_paths=compare_result.deleted_paths,
            start_line=start_line,
            end_line=end_line,
        )
        _count_group_update(group)

    for group in active_groups:
        file_path = group.file_path
        if not file_path:
            continue

        absent = absent_by_path.get(file_path)

        if compare_result.compare_failed:
            if group.resolution_status != ResolutionStatus.addressed:
                if absent is None:
                    if group.closure_blocked_reason != COMPARE_FAILED_REASON:
                        group.closure_blocked_reason = HEAD_CHECK_FAILED_REASON
                        group.resolution_status = ResolutionStatus.still_open
                        _count_group_update(group)
                elif absent is True:
                    if group.closure_blocked_reason != COMPARE_FAILED_REASON:
                        group.closure_blocked_reason = COMPARE_FAILED_REASON
                        group.resolution_status = ResolutionStatus.still_open
                        _count_group_update(group)
                elif absent is False and group.closure_blocked_reason == HEAD_CHECK_FAILED_REASON:
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
                _count_group_update(group)
            continue
        if not path_gone:
            if group.closure_blocked_reason is not None:
                group.closure_blocked_reason = None
                _count_group_update(group)
            continue

        group.closure_blocked_reason = None
        group.resolution_status = ResolutionStatus.addressed
        _count_group_update(group)

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
        group.last_seen_revision_id == current_revision_id and group.resolution_status is not None
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
        for group in groups
        if group.state != GitHubFindingGroupState.superseded
        and _is_hygiene_path_removed_closure(
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
    resolution_rate_pct = round(100.0 * transition_count / denominator, 1) if denominator else 0.0
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
