# backend/app/services/github_pr_resolution_rollup.py
"""PR lifetime resolution rollup manifest — PSR P0."""
from __future__ import annotations

from typing import TypedDict
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import (
    GitHubFindingGroupState,
    GitHubPublishJobStatus,
    ResolutionMethod,
    ResolutionStatus,
)
from app.models.github_finding_group import GitHubFindingGroupORM
from app.models.github_publish_job import GitHubPublishJobORM
from app.models.github_pull_request import GitHubPullRequestRevisionORM
from app.services.github_finding_closure_rules import (
    COMPARE_FAILED_REASON,
    HEAD_CHECK_FAILED_REASON,
)
from app.services.github_publish_formatter import (
    PublishFormatContext,
    display_still_open_prior_count,
    verdict_groups,
)

PR_RESOLUTION_ROLLUP_SCHEMA_VERSION = 1

_LIFETIME_DISCLOSURE = (
    "This is the first Revy review on this pull request. "
    "Lifetime counts include findings that existed before this review."
)


class FilterSnapshot(TypedDict):
    raw_active_before_filters: int
    collapsed_hidden: int
    orphan_never_inlined_hidden: int
    compare_failed_hidden: int


class ResolvedByMethod(TypedDict):
    absent_and_addressed: int
    judge_dismissed: int
    verification_dismissed: int
    human_dismissed: int
    path_removed: int


class PushManifestRef(TypedDict):
    revision_number: int
    transition_count: int


class PrResolutionRollupManifest(TypedDict, total=False):
    schema_version: int
    computed_at_revision_id: str
    revision_number: int
    review_count: int
    raised_count: int
    resolved_count: int
    resolved_by_method: ResolvedByMethod
    still_open_display: int
    still_open_generation: int
    still_open_prior: int
    lifetime_resolution_rate_pct: float | None
    filter_snapshot: FilterSnapshot
    push_manifest_ref: PushManifestRef
    lifetime_disclosure: str | None


def _active_groups(groups: list[GitHubFindingGroupORM]) -> list[GitHubFindingGroupORM]:
    return [group for group in groups if group.state == GitHubFindingGroupState.active]


def _is_lifetime_path_removed_resolution(
    group: GitHubFindingGroupORM,
    *,
    prior_revision_ids_by_resolve_revision: dict[UUID, frozenset[UUID]],
) -> bool:
    resolved_at_revision_id = group.resolved_at_revision_id
    if resolved_at_revision_id is None:
        return False
    prior_revision_ids = prior_revision_ids_by_resolve_revision.get(
        resolved_at_revision_id,
        frozenset(),
    )
    return (
        group.state == GitHubFindingGroupState.resolved
        and group.resolution_method == ResolutionMethod.absent_and_addressed
        and group.last_seen_revision_id is not None
        and group.last_seen_revision_id not in prior_revision_ids
    )


def build_prior_revision_ids_by_resolve_revision(
    revisions: list[GitHubPullRequestRevisionORM],
) -> dict[UUID, frozenset[UUID]]:
    ordered = sorted(revisions, key=lambda revision: revision.revision_number)
    prior_by_revision: dict[UUID, frozenset[UUID]] = {}
    seen: list[UUID] = []
    for revision in ordered:
        prior_by_revision[revision.id] = frozenset(seen)
        seen.append(revision.id)
    return prior_by_revision


def _empty_resolved_by_method() -> ResolvedByMethod:
    return {
        "absent_and_addressed": 0,
        "judge_dismissed": 0,
        "verification_dismissed": 0,
        "human_dismissed": 0,
        "path_removed": 0,
    }


def build_resolved_by_method(
    all_pr_groups: list[GitHubFindingGroupORM],
    *,
    prior_revision_ids_by_resolve_revision: dict[UUID, frozenset[UUID]],
) -> ResolvedByMethod:
    counts = _empty_resolved_by_method()
    for group in all_pr_groups:
        if group.state != GitHubFindingGroupState.resolved:
            continue
        if _is_lifetime_path_removed_resolution(
            group,
            prior_revision_ids_by_resolve_revision=prior_revision_ids_by_resolve_revision,
        ):
            counts["path_removed"] += 1
            continue
        method = group.resolution_method
        if method == ResolutionMethod.absent_and_addressed:
            counts["absent_and_addressed"] += 1
        elif method == ResolutionMethod.judge_dismissed:
            counts["judge_dismissed"] += 1
        elif method == ResolutionMethod.verification_dismissed:
            counts["verification_dismissed"] += 1
        elif method == ResolutionMethod.human_dismissed:
            counts["human_dismissed"] += 1
    return counts


def compute_filter_snapshot(
    raw_pr_active_groups: list[GitHubFindingGroupORM],
    filtered_groups: list[GitHubFindingGroupORM],
    *,
    publishable_fingerprints: set[str],
    collapsed_fingerprints: set[str],
    generation_fingerprints: set[str],
    ever_inlined_fingerprints: set[str] | None,
) -> FilterSnapshot:
    """Build PSR-Q10 filter audit counts for the rollup manifest.

    ``raw_active_before_filters`` counts active groups still eligible for the
    publish surface (excludes ``resolution_status=addressed`` — those are
    already surfaced as addressed, not hidden by collapse/orphan/compare filters).
    """
    filtered_fingerprints = {group.fingerprint for group in filtered_groups}
    raw_active = [
        group
        for group in raw_pr_active_groups
        if group.state == GitHubFindingGroupState.active
        and group.resolution_status != ResolutionStatus.addressed
    ]
    collapsed_hidden = 0
    orphan_hidden = 0
    compare_failed_hidden = 0

    for group in raw_active:
        if group.fingerprint in filtered_fingerprints:
            continue
        if (
            group.fingerprint in collapsed_fingerprints
            and group.fingerprint not in publishable_fingerprints
            and group.fingerprint not in generation_fingerprints
        ):
            collapsed_hidden += 1
            continue
        if (
            ever_inlined_fingerprints is not None
            and group.fingerprint not in ever_inlined_fingerprints
            and group.fingerprint not in generation_fingerprints
        ):
            orphan_hidden += 1
            continue
        if group.closure_blocked_reason in (
            COMPARE_FAILED_REASON,
            HEAD_CHECK_FAILED_REASON,
        ):
            compare_failed_hidden += 1

    return {
        "raw_active_before_filters": len(raw_active),
        "collapsed_hidden": collapsed_hidden,
        "orphan_never_inlined_hidden": orphan_hidden,
        "compare_failed_hidden": compare_failed_hidden,
    }


def build_pr_resolution_rollup(
    ctx: PublishFormatContext,
    all_pr_groups: list[GitHubFindingGroupORM],
    *,
    review_count: int,
    computed_at_revision_id: UUID,
    raw_pr_active_groups: list[GitHubFindingGroupORM],
    publishable_fingerprints: set[str],
    collapsed_fingerprints: set[str],
    prior_revision_ids_by_resolve_revision: dict[UUID, frozenset[UUID]],
) -> PrResolutionRollupManifest:
    """Build manifest v1 from filtered publish ctx and full PR group history."""
    non_superseded = [
        group for group in all_pr_groups if group.state != GitHubFindingGroupState.superseded
    ]
    raised_count = len(non_superseded)
    resolved_count = sum(
        1 for group in non_superseded if group.state == GitHubFindingGroupState.resolved
    )
    verdict = verdict_groups(ctx)
    still_open_display = len(_active_groups(verdict))
    still_open_generation = len(_active_groups(ctx.groups))
    still_open_prior = display_still_open_prior_count(ctx)
    denominator = resolved_count + still_open_display
    lifetime_rate = (
        round(100.0 * resolved_count / denominator, 1) if denominator > 0 else None
    )
    generation_fingerprints = {group.fingerprint for group in ctx.groups}
    ever_inlined = (
        set(ctx.ever_inlined_fingerprints)
        if ctx.ever_inlined_fingerprints is not None
        else None
    )
    filter_snapshot = compute_filter_snapshot(
        raw_pr_active_groups,
        verdict,
        publishable_fingerprints=publishable_fingerprints,
        collapsed_fingerprints=collapsed_fingerprints,
        generation_fingerprints=generation_fingerprints,
        ever_inlined_fingerprints=ever_inlined,
    )
    push_manifest = ctx.resolution_metrics_manifest or {}
    lifetime_disclosure: str | None = None
    if review_count == 1 and raised_count > len(ctx.groups):
        lifetime_disclosure = _LIFETIME_DISCLOSURE

    return {
        "schema_version": PR_RESOLUTION_ROLLUP_SCHEMA_VERSION,
        "computed_at_revision_id": str(computed_at_revision_id),
        "revision_number": ctx.revision_number,
        "review_count": review_count,
        "raised_count": raised_count,
        "resolved_count": resolved_count,
        "resolved_by_method": build_resolved_by_method(
            non_superseded,
            prior_revision_ids_by_resolve_revision=prior_revision_ids_by_resolve_revision,
        ),
        "still_open_display": still_open_display,
        "still_open_generation": still_open_generation,
        "still_open_prior": still_open_prior,
        "lifetime_resolution_rate_pct": lifetime_rate,
        "filter_snapshot": filter_snapshot,
        "push_manifest_ref": {
            "revision_number": ctx.revision_number,
            "transition_count": int(push_manifest.get("transition_count") or 0),
        },
        "lifetime_disclosure": lifetime_disclosure,
    }


async def load_prior_revision_ids_by_resolve_revision(
    session: AsyncSession,
    *,
    pull_request_id: UUID,
) -> dict[UUID, frozenset[UUID]]:
    revisions = list(
        await session.scalars(
            select(GitHubPullRequestRevisionORM).where(
                GitHubPullRequestRevisionORM.pull_request_id == pull_request_id,
            )
        )
    )
    return build_prior_revision_ids_by_resolve_revision(revisions)


async def count_completed_publish_jobs(
    session: AsyncSession,
    *,
    pull_request_id: UUID,
) -> int:
    result = await session.scalar(
        select(func.count())
        .select_from(GitHubPublishJobORM)
        .join(
            GitHubPullRequestRevisionORM,
            GitHubPublishJobORM.revision_id == GitHubPullRequestRevisionORM.id,
        )
        .where(
            GitHubPullRequestRevisionORM.pull_request_id == pull_request_id,
            GitHubPublishJobORM.status == GitHubPublishJobStatus.completed,
        )
    )
    return int(result or 0)


async def review_count_for_in_flight_publish(
    session: AsyncSession,
    *,
    pull_request_id: UUID,
) -> int:
    """Completed publishes on PR plus the publish currently flushing."""
    completed = await count_completed_publish_jobs(session, pull_request_id=pull_request_id)
    return completed + 1
