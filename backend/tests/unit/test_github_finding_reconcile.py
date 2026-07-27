# backend/tests/unit/test_github_finding_reconcile.py
"""GitHub finding reconciliation — R5."""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.constants.enums import (
    FindingCategory,
    FindingSeverity,
    GitHubFindingGroupState,
    GitHubReviewRunStatus,
    ReviewProfile,
)
from app.models.github_finding import GitHubFindingORM
from app.models.github_finding_group import GitHubFindingGroupORM
from app.models.github_pull_request import GitHubPullRequestRevisionORM
from app.models.github_review_run import GitHubReviewRunORM
from app.services.github_finding_reconcile import compute_fingerprint, reconcile_review_run


def test_compute_fingerprint_stable():
    workspace_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    fp1 = compute_fingerprint(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        file_path="app/main.py",
        category=FindingCategory.bug,
        message="  Possible   null  ",
    )
    fp2 = compute_fingerprint(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        file_path="app/main.py",
        category=FindingCategory.bug,
        message="Possible null",
    )
    assert fp1 == fp2


def test_compute_fingerprint_accepts_string_category():
    workspace_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    fp_enum = compute_fingerprint(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        file_path="app/main.py",
        category=FindingCategory.bug,
        message="Possible null",
    )
    fp_str = compute_fingerprint(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        file_path="app/main.py",
        category="bug",
        message="Possible null",
    )
    assert fp_enum == fp_str


@pytest.mark.asyncio
async def test_reconcile_creates_new_group():
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha="abc",
    )
    revision.id = revision_id

    finding = GitHubFindingORM(
        review_run_id=review_run_id,
        workspace_id=workspace_id,
        severity=FindingSeverity.error,
        category=FindingCategory.security,
        title="SQLi",
        message="Unsanitized input",
        file_path="app/db.py",
    )
    finding.id = uuid.uuid4()

    def _add(obj: object) -> None:
        if isinstance(obj, GitHubFindingGroupORM) and obj.id is None:
            obj.id = uuid.uuid4()

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, revision])
    session.scalars = AsyncMock(side_effect=[[finding], []])
    session.scalar = AsyncMock(return_value=None)
    session.add = MagicMock(side_effect=_add)
    session.flush = AsyncMock()

    group_ids = await reconcile_review_run(session, review_run_id=review_run_id)

    assert len(group_ids) == 1
    assert finding.group_id == group_ids[0]


@pytest.mark.asyncio
async def test_reconcile_accepts_string_category_on_finding():
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha="abc",
    )
    revision.id = revision_id

    finding = GitHubFindingORM(
        review_run_id=review_run_id,
        workspace_id=workspace_id,
        severity="error",
        category="security",
        title="SQLi",
        message="Unsanitized input",
        file_path="app/db.py",
    )
    finding.id = uuid.uuid4()

    def _add(obj: object) -> None:
        if isinstance(obj, GitHubFindingGroupORM) and obj.id is None:
            obj.id = uuid.uuid4()

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, revision])
    session.scalars = AsyncMock(side_effect=[[finding], []])
    session.scalar = AsyncMock(return_value=None)
    session.add = MagicMock(side_effect=_add)
    session.flush = AsyncMock()

    group_ids = await reconcile_review_run(session, review_run_id=review_run_id)

    assert len(group_ids) == 1


@pytest.mark.asyncio
async def test_reconcile_same_fingerprint_updates_revision():
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=2,
        head_sha="def",
    )
    revision.id = revision_id

    finding = GitHubFindingORM(
        review_run_id=review_run_id,
        workspace_id=workspace_id,
        severity=FindingSeverity.error,
        category=FindingCategory.security,
        title="SQLi",
        message="Unsanitized input",
        file_path="app/db.py",
    )
    finding.id = uuid.uuid4()

    old_revision_id = uuid.uuid4()
    group = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        fingerprint=compute_fingerprint(
            workspace_id=workspace_id,
            pull_request_id=pull_request_id,
            file_path="app/db.py",
            category=FindingCategory.security,
            message="Unsanitized input",
        ),
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.security,
        title="SQLi",
        message="Unsanitized input",
        file_path="app/db.py",
        last_seen_revision_id=old_revision_id,
    )
    group.id = uuid.uuid4()

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, revision])
    session.scalars = AsyncMock(side_effect=[[finding], []])
    session.scalar = AsyncMock(return_value=group)
    session.flush = AsyncMock()

    await reconcile_review_run(session, review_run_id=review_run_id)

    assert group.last_seen_revision_id == revision_id
    assert group.state == GitHubFindingGroupState.active


@pytest.mark.asyncio
async def test_reconcile_existing_group_supersedes_peers():
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    old_revision_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=3,
        head_sha="ghi",
    )
    revision.id = revision_id

    finding = GitHubFindingORM(
        review_run_id=review_run_id,
        workspace_id=workspace_id,
        severity=FindingSeverity.error,
        category=FindingCategory.security,
        title="SQLi",
        message="Unsanitized input",
        file_path="app/db.py",
    )
    finding.id = uuid.uuid4()

    group = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        fingerprint=compute_fingerprint(
            workspace_id=workspace_id,
            pull_request_id=pull_request_id,
            file_path="app/db.py",
            category=FindingCategory.security,
            message="Unsanitized input",
        ),
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.error,
        category=FindingCategory.security,
        title="SQLi",
        message="Unsanitized input",
        file_path="app/db.py",
        last_seen_revision_id=old_revision_id,
    )
    group.id = uuid.uuid4()

    peer = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        fingerprint="other-fingerprint",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.warning,
        category=FindingCategory.security,
        title="Other",
        message="Other issue",
        file_path="app/db.py",
        last_seen_revision_id=old_revision_id,
    )
    peer.id = uuid.uuid4()

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, revision])
    session.scalars = AsyncMock(side_effect=[[finding], [peer]])
    session.scalar = AsyncMock(return_value=group)
    session.flush = AsyncMock()

    await reconcile_review_run(session, review_run_id=review_run_id)

    assert group.last_seen_revision_id == revision_id
    assert peer.state == GitHubFindingGroupState.superseded


@pytest.mark.asyncio
async def test_reconcile_resolved_group_unchanged():
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=2,
        head_sha="def",
    )
    revision.id = revision_id

    finding = GitHubFindingORM(
        review_run_id=review_run_id,
        workspace_id=workspace_id,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Edge",
        message="Handle empty",
        file_path="app/x.py",
    )
    finding.id = uuid.uuid4()

    old_revision_id = uuid.uuid4()
    group = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=pull_request_id,
        fingerprint=compute_fingerprint(
            workspace_id=workspace_id,
            pull_request_id=pull_request_id,
            file_path="app/x.py",
            category=FindingCategory.bug,
            message="Handle empty",
        ),
        state=GitHubFindingGroupState.resolved,
        severity=FindingSeverity.warning,
        category=FindingCategory.bug,
        title="Edge",
        message="Handle empty",
        file_path="app/x.py",
        last_seen_revision_id=old_revision_id,
    )
    group.id = uuid.uuid4()

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, revision])
    session.scalars = AsyncMock(return_value=[finding])
    session.scalar = AsyncMock(return_value=group)
    session.flush = AsyncMock()

    await reconcile_review_run(session, review_run_id=review_run_id)

    assert group.last_seen_revision_id == old_revision_id
    assert group.state == GitHubFindingGroupState.resolved
    assert finding.group_id == group.id
