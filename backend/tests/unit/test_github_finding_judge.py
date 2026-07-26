# backend/tests/unit/test_github_finding_judge.py
"""GitHub finding judge — R5."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

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
from app.models.github_review_run import GitHubReviewRunORM
from app.services.github_finding_judge import is_judge_candidate, run_judge_for_review_run


def test_is_judge_candidate_error():
    assert is_judge_candidate(severity=FindingSeverity.error, category=FindingCategory.bug)


def test_is_judge_candidate_security_warning():
    assert is_judge_candidate(
        severity=FindingSeverity.warning,
        category=FindingCategory.security,
    )


def test_is_judge_candidate_info_bug_false():
    assert not is_judge_candidate(
        severity=FindingSeverity.info,
        category=FindingCategory.bug,
    )


@pytest.mark.asyncio
async def test_run_judge_skipped_without_api_key():
    session = AsyncMock()
    with patch("app.services.github_finding_judge.settings") as mock_settings:
        mock_settings.anthropic_api_key = None
        count = await run_judge_for_review_run(session, review_run_id=uuid.uuid4())
    assert count == 0


@pytest.mark.asyncio
async def test_run_judge_dismissed_resolves_group():
    review_run_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    group_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=uuid.uuid4(),
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    group = GitHubFindingGroupORM(
        workspace_id=workspace_id,
        pull_request_id=uuid.uuid4(),
        fingerprint="abc",
        state=GitHubFindingGroupState.active,
        severity=FindingSeverity.critical,
        category=FindingCategory.security,
        title="RCE",
        message="Remote code execution",
        file_path="app/run.py",
        last_seen_revision_id=uuid.uuid4(),
    )
    group.id = group_id

    finding = GitHubFindingORM(
        review_run_id=review_run_id,
        workspace_id=workspace_id,
        severity=FindingSeverity.critical,
        category=FindingCategory.security,
        title="RCE",
        message="Remote code execution",
        file_path="app/run.py",
        group_id=group_id,
    )

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, group])
    session.scalars = AsyncMock(return_value=[finding])
    session.scalar = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.flush = AsyncMock()

    with patch("app.services.github_finding_judge.settings") as mock_settings:
        mock_settings.anthropic_api_key = "test-key"
        mock_settings.revy_revision_timeout_standard_seconds = 900
        with patch(
            "app.services.github_finding_judge.anthropic_review.judge_finding",
            AsyncMock(return_value={"outcome": "dismissed", "notes": "false positive"}),
        ):
            count = await run_judge_for_review_run(session, review_run_id=review_run_id)

    assert count == 1
    assert group.state == GitHubFindingGroupState.resolved
