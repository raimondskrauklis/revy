# backend/tests/unit/test_github_review_observability_checkpoint.py
"""Pipeline observability P0 — checkpoint commit after retrieve."""
import uuid
from unittest.mock import AsyncMock

import pytest

from app.constants.enums import GitHubReviewRunStatus, ReviewProfile
from app.models.github_review_run import GitHubReviewRunORM
from app.services.review_run_observability import commit_review_run_observability_checkpoint


@pytest.mark.asyncio
async def test_checkpoint_commits_timing_stats_and_failure_stage():
    run = GitHubReviewRunORM(
        revision_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        status=GitHubReviewRunStatus.processing,
        profile=ReviewProfile.standard,
    )
    session = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()

    await commit_review_run_observability_checkpoint(
        session,
        run,
        retrieve_duration_ms=1500,
        compare_ms=100,
        supplemental_ms=200,
    )

    assert run.failure_stage == "retrieve"
    assert run.timing_stats == {
        "stats_version": 1,
        "retrieve_ms": 1500,
        "compare_ms": 100,
        "supplemental_ms": 200,
    }
    session.commit.assert_awaited_once()
    session.refresh.assert_awaited_once_with(run)
