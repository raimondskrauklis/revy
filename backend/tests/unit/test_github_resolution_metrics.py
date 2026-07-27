# backend/tests/unit/test_github_resolution_metrics.py
"""Resolution metrics — RQ6."""
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.constants.enums import (
    FindingCategory,
    FindingSeverity,
    GitHubFindingGroupState,
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
        start_line=10,
        end_line=10,
    )
    assert status == ResolutionStatus.still_open


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
        AsyncMock(return_value={"app/handler.py": compare.files[0].patch}),
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
    session.flush.assert_awaited()
