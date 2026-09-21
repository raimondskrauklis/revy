# backend/tests/unit/test_autostart_credit_blocked.py
"""Autostart pipeline returns fail_pipeline_check when credit limit reached."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.constants.enums import GitHubIndexJobStatus, GitHubIndexJobTriggerSource
from app.core.exceptions import ForbiddenError
from app.services.review_pipeline import prepare_review_after_index


@pytest.fixture
def workspace_id():
    return uuid.uuid4()


@pytest.fixture
def mock_session():
    return AsyncMock()


@pytest.mark.asyncio
async def test_forbidden_error_returns_fail_pipeline_check(mock_session, workspace_id):
    """When create_review_run raises ForbiddenError, pipeline returns fail_pipeline_check=True."""
    from app.constants.enums import GitHubPullRequestState

    # Make pipeline reach the create_review_run call by mocking all pre-checks
    with (
        patch(
            "app.services.review_pipeline.resolve_pending_review_run_id",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "app.services.review_pipeline.is_authoritative_for_pull_request_head",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "app.services.review_pipeline.create_review_run",
            new_callable=AsyncMock,
            side_effect=ForbiddenError(
                message="Credit limit reached",
                error_code="credit_limit_reached",
                details={"completed_runs": 25, "run_limit": 25},
            ),
        ),
    ):
        from app.models.github_index_job import GitHubIndexJobORM

        job = GitHubIndexJobORM(
            status=GitHubIndexJobStatus.completed,
            trigger_source=GitHubIndexJobTriggerSource.autostart,
        )
        job.id = uuid.uuid4()
        job.workspace_id = workspace_id
        job.revision_id = uuid.uuid4()

        # Mock session.get to return revision + pull_request
        revision = MagicMock()
        revision.pull_request_id = uuid.uuid4()
        pr = MagicMock()
        pr.repository_id = uuid.uuid4()
        pr.is_draft = False
        pr.state = GitHubPullRequestState.open

        async def get_side_effect(model, key):
            if hasattr(revision, 'pull_request_id'):
                return revision
            return pr

        mock_session.get = AsyncMock()
        mock_session.get.side_effect = [revision, pr]

        outcome = await prepare_review_after_index(mock_session, job)

        assert outcome.fail_pipeline_check is True
        assert outcome.pipeline_check_summary == "credit_limit_reached"


@pytest.mark.asyncio
async def test_non_credit_forbidden_error_returns_description(mock_session, workspace_id):
    """Non-credit ForbiddenError should still fail pipeline with error description."""
    from app.constants.enums import GitHubPullRequestState

    with (
        patch(
            "app.services.review_pipeline.resolve_pending_review_run_id",
            new_callable=AsyncMock,
            return_value=None,
        ),
        patch(
            "app.services.review_pipeline.is_authoritative_for_pull_request_head",
            new_callable=AsyncMock,
            return_value=True,
        ),
        patch(
            "app.services.review_pipeline.create_review_run",
            new_callable=AsyncMock,
            side_effect=ForbiddenError(
                message="Plan upgrade required",
                error_code="plan_upgrade_required",
                details={"feature": "some_feature", "required_plan": "pro"},
            ),
        ),
    ):
        from app.models.github_index_job import GitHubIndexJobORM

        job = GitHubIndexJobORM(
            status=GitHubIndexJobStatus.completed,
            trigger_source=GitHubIndexJobTriggerSource.autostart,
        )
        job.id = uuid.uuid4()
        job.workspace_id = workspace_id
        job.revision_id = uuid.uuid4()

        revision = MagicMock()
        revision.pull_request_id = uuid.uuid4()
        pr = MagicMock()
        pr.repository_id = uuid.uuid4()
        pr.is_draft = False
        pr.state = GitHubPullRequestState.open

        mock_session.get = AsyncMock()
        mock_session.get.side_effect = [revision, pr]

        outcome = await prepare_review_after_index(mock_session, job)

        assert outcome.fail_pipeline_check is True
        assert outcome.pipeline_check_summary == "plan_upgrade_required"