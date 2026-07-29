# backend/tests/unit/test_github_resolution_metrics.py
"""Resolution metrics — RQ6."""
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.constants.enums import (
    FindingCategory,
    FindingSeverity,
    GitHubFindingGroupState,
    ResolutionMethod,
    ResolutionStatus,
)
from app.integrations.github_api import CompareCommitsResult, CompareFileChange
from app.models.github_finding_group import GitHubFindingGroupORM
from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
from app.services import github_resolution_metrics


def test_patch_touches_line_region_detects_modified_line():
    patch = "@@ -10,3 +10,4 @@\n def foo():\n-    old()\n+    new_call()\n     return x\n"
    assert github_resolution_metrics.patch_touches_line_region(
        patch,
        start_line=11,
        end_line=11,
    )


def test_patch_touches_line_region_false_when_unchanged_region():
    patch = "@@ -1,3 +1,3 @@\n unchanged\n"
    assert not github_resolution_metrics.patch_touches_line_region(
        patch,
        start_line=99,
        end_line=99,
    )


def test_resolve_group_resolution_status_judge_dismissed():
    group = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=uuid.uuid4(),
        fingerprint="a",
        state=GitHubFindingGroupState.resolved,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="T",
        message="M",
        file_path="app/a.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    status = github_resolution_metrics.resolve_group_resolution_status(
        group=group,
        patches_by_file={},
        removed_paths=frozenset(),
        start_line=1,
        end_line=1,
    )
    assert status == ResolutionStatus.judge_dismissed


def test_resolve_group_resolution_status_addressed():
    group = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=uuid.uuid4(),
        fingerprint="a",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="T",
        message="M",
        file_path="app/a.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    patch = "@@ -5,1 +5,1 @@\n-old\n+new\n"
    status = github_resolution_metrics.resolve_group_resolution_status(
        group=group,
        patches_by_file={"app/a.py": patch},
        removed_paths=frozenset(),
        start_line=5,
        end_line=5,
    )
    assert status == ResolutionStatus.addressed


def test_resolve_group_resolution_status_still_open():
    group = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=uuid.uuid4(),
        fingerprint="a",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="T",
        message="M",
        file_path="app/other.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    status = github_resolution_metrics.resolve_group_resolution_status(
        group=group,
        patches_by_file={"app/a.py": "@@ -1 +1 @@\n+x\n"},
        removed_paths=frozenset(),
        start_line=10,
        end_line=10,
    )
    assert status == ResolutionStatus.still_open


def test_resolve_group_resolution_status_addressed_when_file_removed():
    group = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=uuid.uuid4(),
        fingerprint="a",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="T",
        message="M",
        file_path="app/deleted.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    status = github_resolution_metrics.resolve_group_resolution_status(
        group=group,
        patches_by_file={},
        removed_paths=frozenset({"app/deleted.py"}),
        start_line=12,
        end_line=12,
    )
    assert status == ResolutionStatus.addressed


def test_resolve_group_resolution_status_addressed_when_file_renamed_old_path():
    group = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=uuid.uuid4(),
        fingerprint="a",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="T",
        message="M",
        file_path="app/old_name.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    status = github_resolution_metrics.resolve_group_resolution_status(
        group=group,
        patches_by_file={"app/new_name.py": "@@ -1 +1 @@\n+x\n"},
        removed_paths=frozenset({"app/old_name.py"}),
        start_line=4,
        end_line=4,
    )
    assert status == ResolutionStatus.addressed


@pytest.mark.asyncio
async def test_apply_resolution_status_for_synchronize_updates_prior_groups():
    pull_request_id = uuid.uuid4()
    prior_revision_id = uuid.uuid4()
    new_revision_id = uuid.uuid4()

    pull_request = GitHubPullRequestORM(
        repository_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        installation_id=uuid.uuid4(),
        github_pull_request_id=1,
        number=1,
        title="PR",
        state="open",
        head_sha="newsha",
        head_ref="feature",
        base_ref="main",
        revision_count=2,
    )
    pull_request.id = pull_request_id

    prior_revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha="oldsha",
        base_sha="base1",
    )
    prior_revision.id = prior_revision_id

    new_revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=2,
        head_sha="newsha",
        base_sha="base1",
    )
    new_revision.id = new_revision_id

    group_id = uuid.uuid4()
    group = GitHubFindingGroupORM(
        workspace_id=pull_request.workspace_id,
        pull_request_id=pull_request_id,
        fingerprint="fp",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="Bug",
        message="msg",
        file_path="app/handler.py",
        last_seen_revision_id=prior_revision_id,
    )
    group.id = group_id

    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[prior_revision])
    session.scalars = AsyncMock(return_value=[group])
    session.flush = AsyncMock()

    compare = CompareCommitsResult(
        files=(
            CompareFileChange(
                filename="app/handler.py",
                status="modified",
                patch="@@ -12,1 +12,1 @@\n-old\n+fixed\n",
            ),
        )
    )

    with patch(
        "app.services.github_resolution_metrics._fetch_compare_patches",
        AsyncMock(
            return_value=type(
                "CompareResult",
                (),
                {"patches_by_file": {"app/handler.py": compare.files[0].patch}, "compare_failed": False, "removed_paths": frozenset()},
            )()
        ),
    ):
        with patch(
            "app.services.github_resolution_metrics._latest_finding_lines",
            AsyncMock(return_value=(12, 12)),
        ):
            updated = await github_resolution_metrics.apply_resolution_status_for_synchronize(
                session,
                pull_request=pull_request,
                new_revision=new_revision,
            )

    assert updated == 1
    assert group.resolution_status == ResolutionStatus.addressed
    assert group.closure_blocked_reason is None
    session.flush.assert_awaited()


@pytest.mark.asyncio
async def test_apply_resolution_status_for_synchronize_stamps_compare_failed():
    pull_request_id = uuid.uuid4()
    prior_revision_id = uuid.uuid4()
    new_revision_id = uuid.uuid4()

    pull_request = GitHubPullRequestORM(
        repository_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        installation_id=uuid.uuid4(),
        github_pull_request_id=1,
        number=1,
        title="PR",
        state="open",
        head_sha="newsha",
        head_ref="feature",
        base_ref="main",
        revision_count=2,
    )
    pull_request.id = pull_request_id

    prior_revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha="oldsha",
        base_sha="base1",
    )
    prior_revision.id = prior_revision_id

    new_revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=2,
        head_sha="newsha",
        base_sha="base1",
    )
    new_revision.id = new_revision_id

    group = GitHubFindingGroupORM(
        workspace_id=pull_request.workspace_id,
        pull_request_id=pull_request_id,
        fingerprint="fp",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="Bug",
        message="msg",
        file_path="app/handler.py",
        last_seen_revision_id=prior_revision_id,
    )

    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[prior_revision])
    session.scalars = AsyncMock(return_value=[group])
    session.flush = AsyncMock()

    failed_result = type(
        "CompareResult",
        (),
        {"patches_by_file": {}, "compare_failed": True, "removed_paths": frozenset()},
    )()

    with patch(
        "app.services.github_resolution_metrics._fetch_compare_patches",
        AsyncMock(return_value=failed_result),
    ):
        updated = await github_resolution_metrics.apply_resolution_status_for_synchronize(
            session,
            pull_request=pull_request,
            new_revision=new_revision,
        )

    assert updated == 1
    assert group.resolution_status == ResolutionStatus.still_open
    assert group.closure_blocked_reason == "compare_failed"


@pytest.mark.asyncio
async def test_apply_resolution_status_for_synchronize_stamps_addressed_on_file_deletion():
    pull_request_id = uuid.uuid4()
    prior_revision_id = uuid.uuid4()
    new_revision_id = uuid.uuid4()

    pull_request = GitHubPullRequestORM(
        repository_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        installation_id=uuid.uuid4(),
        github_pull_request_id=1,
        number=1,
        title="PR",
        state="open",
        head_sha="newsha",
        head_ref="feature",
        base_ref="main",
        revision_count=2,
    )
    pull_request.id = pull_request_id

    prior_revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha="oldsha",
        base_sha="base1",
    )
    prior_revision.id = prior_revision_id

    new_revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=2,
        head_sha="newsha",
        base_sha="base1",
    )
    new_revision.id = new_revision_id

    group = GitHubFindingGroupORM(
        workspace_id=pull_request.workspace_id,
        pull_request_id=pull_request_id,
        fingerprint="fp",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="Bug",
        message="msg",
        file_path="backend/tests/fixtures/fr_dogfood/probe_module.py",
        last_seen_revision_id=prior_revision_id,
    )

    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[prior_revision])
    session.scalars = AsyncMock(return_value=[group])
    session.flush = AsyncMock()

    with patch(
        "app.services.github_resolution_metrics._fetch_compare_patches",
        AsyncMock(
            return_value=type(
                "CompareResult",
                (),
                {
                    "patches_by_file": {},
                    "compare_failed": False,
                    "removed_paths": frozenset(
                        {"backend/tests/fixtures/fr_dogfood/probe_module.py"}
                    ),
                },
            )()
        ),
    ):
        with patch(
            "app.services.github_resolution_metrics._latest_finding_lines",
            AsyncMock(return_value=(8, 8)),
        ):
            updated = await github_resolution_metrics.apply_resolution_status_for_synchronize(
                session,
                pull_request=pull_request,
                new_revision=new_revision,
            )

    assert updated == 1
    assert group.resolution_status == ResolutionStatus.addressed
    assert group.closure_blocked_reason is None


def test_build_resolution_pass_manifest_counts_transitions():
    prior_revision_id = uuid.uuid4()
    current_revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()

    addressed = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=pull_request_id,
        fingerprint="a",
        state=GitHubFindingGroupState.resolved,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="Fixed",
        message="M",
        file_path="app/a.py",
        last_seen_revision_id=prior_revision_id,
        resolution_method=ResolutionMethod.absent_and_addressed,
        resolved_at_revision_id=current_revision_id,
    )
    judge_dismissed = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=pull_request_id,
        fingerprint="b",
        state=GitHubFindingGroupState.resolved,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="Dismissed",
        message="M",
        file_path="app/b.py",
        last_seen_revision_id=prior_revision_id,
        resolution_method=ResolutionMethod.judge_dismissed,
        resolved_at_revision_id=current_revision_id,
    )
    still_open = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=pull_request_id,
        fingerprint="c",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Open",
        message="M",
        file_path="app/c.py",
        last_seen_revision_id=prior_revision_id,
        resolution_status=ResolutionStatus.still_open,
    )
    compare_failed = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=pull_request_id,
        fingerprint="d",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Blocked",
        message="M",
        file_path="app/d.py",
        last_seen_revision_id=prior_revision_id,
        resolution_status=ResolutionStatus.still_open,
        closure_blocked_reason="compare_failed",
    )
    pre_sync_resolved = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=pull_request_id,
        fingerprint="e",
        state=GitHubFindingGroupState.resolved,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Old",
        message="M",
        file_path="app/e.py",
        last_seen_revision_id=prior_revision_id,
        resolution_method=ResolutionMethod.judge_dismissed,
        resolved_at_revision_id=uuid.uuid4(),
    )

    manifest = github_resolution_metrics.build_resolution_pass_manifest(
        [addressed, judge_dismissed, still_open, compare_failed, pre_sync_resolved],
        prior_revision_ids=frozenset({prior_revision_id}),
        current_revision_id=current_revision_id,
    )

    assert manifest["transitions_addressed"] == 1
    assert manifest["transitions_dismissed"]["judge_dismissed"] == 1
    assert manifest["transition_count"] == 2
    assert manifest["denominator_active_prior"] == 3
    assert manifest["resolution_rate_pct"] == 66.7
    assert manifest["compare_failed_count"] == 1


def test_build_resolution_pass_manifest_includes_rereported_stamp_cohort():
    prior_revision_id = uuid.uuid4()
    current_revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()

    rereported = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=pull_request_id,
        fingerprint="r",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="Re-reported",
        message="M",
        file_path="app/r.py",
        last_seen_revision_id=current_revision_id,
        resolution_status=ResolutionStatus.still_open,
    )

    manifest = github_resolution_metrics.build_resolution_pass_manifest(
        [rereported],
        prior_revision_ids=frozenset({prior_revision_id}),
        current_revision_id=current_revision_id,
    )

    assert manifest["denominator_active_prior"] == 1
    assert manifest["still_open_count"] == 1


def test_build_resolution_pass_manifest_includes_unpublished_gap_last_seen():
    prior_revision_id = uuid.uuid4()
    gap_revision_id = uuid.uuid4()
    current_revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()

    gap_group = GitHubFindingGroupORM(
        workspace_id=uuid.uuid4(),
        pull_request_id=pull_request_id,
        fingerprint="gap",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Gap",
        message="M",
        file_path="app/gap.py",
        last_seen_revision_id=gap_revision_id,
        resolution_status=ResolutionStatus.still_open,
    )

    manifest = github_resolution_metrics.build_resolution_pass_manifest(
        [gap_group],
        prior_revision_ids=frozenset({prior_revision_id, gap_revision_id}),
        current_revision_id=current_revision_id,
    )

    assert manifest["denominator_active_prior"] == 1
    assert manifest["still_open_count"] == 1


@pytest.mark.asyncio
async def test_compute_resolution_transitions_queries_groups():
    prior_revision_id = uuid.uuid4()
    current_revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()

    pull_request = GitHubPullRequestORM(
        repository_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        installation_id=uuid.uuid4(),
        github_pull_request_id=1,
        number=1,
        title="PR",
        state="open",
        head_sha="newsha",
        head_ref="feature",
        base_ref="main",
        revision_count=2,
    )
    pull_request.id = pull_request_id

    prior_revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha="oldsha",
        base_sha="base1",
    )
    prior_revision.id = prior_revision_id

    current_revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=2,
        head_sha="newsha",
        base_sha="base1",
    )
    current_revision.id = current_revision_id

    session = AsyncMock()
    session.scalars = AsyncMock(return_value=[])

    manifest = await github_resolution_metrics.compute_resolution_transitions(
        session,
        pull_request=pull_request,
        prior_revision=prior_revision,
        current_revision=current_revision,
    )

    assert manifest["denominator_active_prior"] == 0
    assert manifest["transition_count"] == 0


@pytest.mark.asyncio
async def test_get_last_published_prior_revision_returns_completed_publish_prior():
    pull_request_id = uuid.uuid4()
    published_prior = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha="published",
        base_sha="base",
    )
    current_revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=3,
        head_sha="head",
        base_sha="base",
    )
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=published_prior)

    result = await github_resolution_metrics.get_last_published_prior_revision(
        session,
        pull_request_id=pull_request_id,
        current_revision=current_revision,
    )

    assert result is published_prior
    session.scalar.assert_awaited_once()


@pytest.mark.asyncio
async def test_apply_resolution_status_for_synchronize_skipped_not_head_uses_last_published():
    pull_request_id = uuid.uuid4()
    prior_revision_id = uuid.uuid4()
    new_revision_id = uuid.uuid4()

    pull_request = GitHubPullRequestORM(
        repository_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        installation_id=uuid.uuid4(),
        github_pull_request_id=1,
        number=1,
        title="PR",
        state="open",
        head_sha="newsha",
        head_ref="feature",
        base_ref="main",
        revision_count=3,
    )
    pull_request.id = pull_request_id

    published_prior = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha="published",
        base_sha="base1",
    )
    published_prior.id = prior_revision_id

    new_revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=3,
        head_sha="newsha",
        base_sha="base1",
    )
    new_revision.id = new_revision_id

    group = GitHubFindingGroupORM(
        workspace_id=pull_request.workspace_id,
        pull_request_id=pull_request_id,
        fingerprint="fp",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.bug,
        title="Bug",
        message="msg",
        file_path="app/handler.py",
        last_seen_revision_id=prior_revision_id,
    )

    session = AsyncMock()
    session.scalars = AsyncMock(return_value=[group])
    session.flush = AsyncMock()

    with patch(
        "app.services.github_resolution_metrics.get_last_published_prior_revision",
        AsyncMock(return_value=published_prior),
    ):
        with patch(
            "app.services.github_resolution_metrics._fetch_compare_patches",
            AsyncMock(
                return_value=type(
                    "CompareResult",
                    (),
                    {
                        "patches_by_file": {
                            "app/handler.py": "@@ -12,1 +12,1 @@\n-old\n+fixed\n"
                        },
                        "compare_failed": False,
                        "removed_paths": frozenset(),
                    },
                )()
            ),
        ):
            with patch(
                "app.services.github_resolution_metrics._latest_finding_lines",
                AsyncMock(return_value=(12, 12)),
            ):
                updated = await github_resolution_metrics.apply_resolution_status_for_synchronize(
                    session,
                    pull_request=pull_request,
                    new_revision=new_revision,
                )

    assert updated == 1
    assert group.resolution_status == ResolutionStatus.addressed
