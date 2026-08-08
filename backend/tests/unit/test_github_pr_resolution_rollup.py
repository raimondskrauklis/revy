# backend/tests/unit/test_github_pr_resolution_rollup.py
"""Unit tests for PR resolution rollup manifest — PSR P0."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock

import pytest

from app.constants.enums import (
    FindingCategory,
    FindingSeverity,
    GitHubFindingGroupState,
    ResolutionMethod,
    ResolutionStatus,
)
from app.models.github_finding_group import GitHubFindingGroupORM
from app.services.github_pr_resolution_rollup import (
    PR_RESOLUTION_ROLLUP_SCHEMA_VERSION,
    build_pr_resolution_rollup,
    build_resolved_by_method,
    compute_filter_snapshot,
    count_completed_publish_jobs,
    review_count_for_in_flight_publish,
)
from app.services.github_publish_formatter import (
    PublishFormatContext,
    apply_publish_summary_thread_collapse,
    display_still_open_prior_count,
    verdict_groups,
)


def _group(**kwargs) -> GitHubFindingGroupORM:
    defaults = {
        "workspace_id": uuid.uuid4(),
        "pull_request_id": uuid.uuid4(),
        "fingerprint": f"fp-{uuid.uuid4().hex[:8]}",
        "state": GitHubFindingGroupState.active,
        "severity": FindingSeverity.warning,
        "category": FindingCategory.bug,
        "title": "Issue",
        "message": "Details",
        "file_path": "app/main.py",
        "last_seen_revision_id": uuid.uuid4(),
        "resolution_status": ResolutionStatus.still_open,
    }
    defaults.update(kwargs)
    return GitHubFindingGroupORM(**defaults)


def _ctx(
    groups: list[GitHubFindingGroupORM],
    *,
    pr_active_groups: list[GitHubFindingGroupORM] | None = None,
    revision_number: int = 1,
) -> PublishFormatContext:
    return PublishFormatContext(
        pull_request_id=uuid.uuid4(),
        pull_request_number=42,
        head_sha="abc123",
        revision_number=revision_number,
        groups=groups,
        pr_active_groups=pr_active_groups,
        resolution_metrics_manifest={"transition_count": 2},
    )


def test_build_pr_resolution_rollup_revision_one():
    generation = _group(fingerprint="gen-1")
    ctx = _ctx([generation], pr_active_groups=[generation])
    rollup = build_pr_resolution_rollup(
        ctx,
        [generation],
        review_count=1,
        computed_at_revision_id=uuid.uuid4(),
        raw_pr_active_groups=[generation],
        publishable_fingerprints={"gen-1"},
        collapsed_fingerprints=set(),
        prior_revision_ids_by_resolve_revision={},
    )
    assert rollup["schema_version"] == PR_RESOLUTION_ROLLUP_SCHEMA_VERSION
    assert rollup["raised_count"] == 1
    assert rollup["resolved_count"] == 0
    assert rollup["still_open_display"] == 1
    assert rollup["still_open_generation"] == 1
    assert rollup["still_open_prior"] == 0
    assert rollup["lifetime_resolution_rate_pct"] == 0.0
    assert rollup["lifetime_disclosure"] is None


def test_build_pr_resolution_rollup_legacy_pr_disclosure():
    prior = _group(fingerprint="legacy-prior")
    generation = _group(fingerprint="gen-new")
    ctx = _ctx([generation], pr_active_groups=[prior, generation], revision_number=3)
    rollup = build_pr_resolution_rollup(
        ctx,
        [prior, generation],
        review_count=1,
        computed_at_revision_id=uuid.uuid4(),
        raw_pr_active_groups=[prior, generation],
        publishable_fingerprints={"gen-new"},
        collapsed_fingerprints=set(),
        prior_revision_ids_by_resolve_revision={},
    )
    assert rollup["raised_count"] == 2
    assert rollup["lifetime_disclosure"] is not None


def test_still_open_display_matches_block_two_row_count():
    prior = _group(fingerprint="prior-1")
    generation = _group(fingerprint="gen-1")
    filtered = [prior, generation]
    ctx = _ctx([generation], pr_active_groups=filtered)
    rollup = build_pr_resolution_rollup(
        ctx,
        filtered,
        review_count=2,
        computed_at_revision_id=uuid.uuid4(),
        raw_pr_active_groups=filtered,
        publishable_fingerprints={"gen-1"},
        collapsed_fingerprints=set(),
        prior_revision_ids_by_resolve_revision={},
    )
    from app.services.github_publish_formatter import _active_groups

    assert rollup["still_open_display"] == len(_active_groups(verdict_groups(ctx)))


def test_still_open_prior_matches_display_still_open_prior_count():
    prior = _group(fingerprint="prior-only")
    generation = _group(fingerprint="gen-1")
    filtered = [prior, generation]
    ctx = _ctx([generation], pr_active_groups=filtered)
    rollup = build_pr_resolution_rollup(
        ctx,
        filtered,
        review_count=2,
        computed_at_revision_id=uuid.uuid4(),
        raw_pr_active_groups=filtered,
        publishable_fingerprints={"gen-1"},
        collapsed_fingerprints=set(),
        prior_revision_ids_by_resolve_revision={},
    )
    assert rollup["still_open_prior"] == display_still_open_prior_count(ctx)


def test_lifetime_resolution_rate_hand_count():
    resolved = _group(
        fingerprint="resolved-1",
        state=GitHubFindingGroupState.resolved,
        resolution_method=ResolutionMethod.judge_dismissed,
        resolved_at_revision_id=uuid.uuid4(),
        last_seen_revision_id=uuid.uuid4(),
    )
    active = _group(fingerprint="active-1")
    ctx = _ctx([], pr_active_groups=[active])
    rollup = build_pr_resolution_rollup(
        ctx,
        [resolved, active],
        review_count=2,
        computed_at_revision_id=uuid.uuid4(),
        raw_pr_active_groups=[active],
        publishable_fingerprints=set(),
        collapsed_fingerprints=set(),
        prior_revision_ids_by_resolve_revision={},
    )
    assert rollup["resolved_count"] == 1
    assert rollup["still_open_display"] == 1
    assert rollup["lifetime_resolution_rate_pct"] == 50.0


def test_build_resolved_by_method_path_removed_bucket():
    current_revision_id = uuid.uuid4()
    prior_revision_id = uuid.uuid4()
    aged_revision_id = uuid.uuid4()
    path_removed = _group(
        fingerprint="path-removed",
        state=GitHubFindingGroupState.resolved,
        resolution_method=ResolutionMethod.absent_and_addressed,
        resolved_at_revision_id=current_revision_id,
        last_seen_revision_id=aged_revision_id,
    )
    normal = _group(
        fingerprint="normal",
        state=GitHubFindingGroupState.resolved,
        resolution_method=ResolutionMethod.absent_and_addressed,
        resolved_at_revision_id=current_revision_id,
        last_seen_revision_id=prior_revision_id,
    )
    prior_map = {current_revision_id: frozenset({prior_revision_id})}
    counts = build_resolved_by_method(
        [path_removed, normal],
        prior_revision_ids_by_resolve_revision=prior_map,
    )
    assert counts["path_removed"] == 1
    assert counts["absent_and_addressed"] == 1


def test_compute_filter_snapshot_collapsed_hidden():
    collapsed = _group(fingerprint="collapsed-fp")
    generation = _group(fingerprint="gen-1")
    raw = [collapsed, generation]
    filtered = [generation]
    snapshot = compute_filter_snapshot(
        raw,
        filtered,
        publishable_fingerprints={"gen-1"},
        collapsed_fingerprints={"collapsed-fp"},
        generation_fingerprints={"gen-1"},
        ever_inlined_fingerprints={"collapsed-fp"},
    )
    assert snapshot["collapsed_hidden"] == 1
    assert snapshot["raw_active_before_filters"] == 2


def test_post_collapse_rollup_matches_filtered_ctx():
    prior = _group(fingerprint="prior-collapsed")
    generation = _group(fingerprint="gen-1")
    raw_pr_active = [prior, generation]
    ctx = _ctx(
        [generation],
        pr_active_groups=raw_pr_active,
        revision_number=2,
    )
    check = "check"
    issue = "issue body"
    apply_publish_summary_thread_collapse(
        check,
        issue,
        ctx,
        publishable_fingerprints={"gen-1"},
        collapsed_fingerprints={"prior-collapsed"},
    )
    filtered = [generation]
    filtered_ctx = PublishFormatContext(
        pull_request_id=ctx.pull_request_id,
        pull_request_number=ctx.pull_request_number,
        head_sha=ctx.head_sha,
        revision_number=ctx.revision_number,
        groups=ctx.groups,
        pr_active_groups=filtered,
        resolution_metrics_manifest=ctx.resolution_metrics_manifest,
    )
    revision_id = uuid.uuid4()
    expected = build_pr_resolution_rollup(
        filtered_ctx,
        raw_pr_active,
        review_count=2,
        computed_at_revision_id=revision_id,
        raw_pr_active_groups=raw_pr_active,
        publishable_fingerprints={"gen-1"},
        collapsed_fingerprints={"prior-collapsed"},
        prior_revision_ids_by_resolve_revision={},
    )
    actual = build_pr_resolution_rollup(
        filtered_ctx,
        raw_pr_active,
        review_count=2,
        computed_at_revision_id=revision_id,
        raw_pr_active_groups=raw_pr_active,
        publishable_fingerprints={"gen-1"},
        collapsed_fingerprints={"prior-collapsed"},
        prior_revision_ids_by_resolve_revision={},
    )
    assert actual["still_open_display"] == expected["still_open_display"] == 1
    assert actual["filter_snapshot"]["collapsed_hidden"] == 1


@pytest.mark.asyncio
async def test_count_completed_publish_jobs():
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=3)
    count = await count_completed_publish_jobs(session, pull_request_id=uuid.uuid4())
    assert count == 3


@pytest.mark.asyncio
async def test_review_count_for_in_flight_publish_includes_current():
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=2)
    count = await review_count_for_in_flight_publish(session, pull_request_id=uuid.uuid4())
    assert count == 3
