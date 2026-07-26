# backend/tests/unit/test_github_review_routes.py
"""Review routes — R4."""
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.api.v1.workspaces.installation_review import (
    get_review_run_for_revision,
    post_review_pull_request_revision,
)
from app.constants.enums import GitHubReviewJudgeStatus, GitHubReviewRunStatus, ReviewProfile
from app.core.exceptions import ConflictError, ServiceUnavailableError
from app.models.github_review_run import GitHubReviewRunORM
from app.schemas.github_review import ReviewTriggerRequest


@pytest.mark.asyncio
async def test_post_review_pull_request_revision_queues_run():
    workspace_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    session = AsyncMock()
    session.commit = AsyncMock()
    current_user = AsyncMock()
    current_user.workspace_id = workspace_id
    current_user.user_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.pending,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = uuid.uuid4()
    run.created_at = datetime.now(UTC)
    run.updated_at = datetime.now(UTC)
    run.judge_status = GitHubReviewJudgeStatus.not_applicable
    run.judge_escalation_candidate_count = 0

    with patch("app.api.v1.workspaces.installation_review.require_permission"):
        with patch("app.api.v1.workspaces.installation_review.require_same_workspace"):
            with patch(
                "app.api.v1.workspaces.installation_review.create_review_run",
                AsyncMock(return_value=run),
            ):
                with patch(
                    "app.api.v1.workspaces.installation_review.record_audit",
                    AsyncMock(),
                ):
                    with patch(
                        "app.api.v1.workspaces.installation_review.enqueue_review_run",
                    ) as enqueue_mock:
                        response = await post_review_pull_request_revision(
                            workspace_id=workspace_id,
                            repository_id=repository_id,
                            pull_request_id=pull_request_id,
                            revision_id=revision_id,
                            body=ReviewTriggerRequest(),
                            current_user=current_user,
                            session=session,
                            idempotent=None,
                        )

    enqueue_mock.assert_called_once_with(run.id, profile=ReviewProfile.standard)
    assert response.data.status == GitHubReviewRunStatus.pending


@pytest.mark.asyncio
async def test_post_review_index_required_raises():
    workspace_id = uuid.uuid4()
    session = AsyncMock()
    current_user = AsyncMock()
    current_user.workspace_id = workspace_id
    current_user.user_id = uuid.uuid4()

    with patch("app.api.v1.workspaces.installation_review.require_permission"):
        with patch("app.api.v1.workspaces.installation_review.require_same_workspace"):
            with patch(
                "app.api.v1.workspaces.installation_review.create_review_run",
                AsyncMock(
                    side_effect=ConflictError(
                        message="Revision must be indexed before review",
                        error_code="index_required",
                    )
                ),
            ):
                with pytest.raises(ConflictError) as exc:
                    await post_review_pull_request_revision(
                        workspace_id=workspace_id,
                        repository_id=uuid.uuid4(),
                        pull_request_id=uuid.uuid4(),
                        revision_id=uuid.uuid4(),
                        body=ReviewTriggerRequest(),
                        current_user=current_user,
                        session=session,
                        idempotent=None,
                    )
    assert exc.value.error_code == "index_required"


@pytest.mark.asyncio
async def test_post_review_disabled_llm_raises():
    workspace_id = uuid.uuid4()
    session = AsyncMock()
    current_user = AsyncMock()
    current_user.workspace_id = workspace_id
    current_user.user_id = uuid.uuid4()

    with patch("app.api.v1.workspaces.installation_review.require_permission"):
        with patch("app.api.v1.workspaces.installation_review.require_same_workspace"):
            with patch(
                "app.api.v1.workspaces.installation_review.create_review_run",
                AsyncMock(
                    side_effect=ServiceUnavailableError(
                        message="LLM API is not configured",
                        error_code="llm_disabled",
                    )
                ),
            ):
                with pytest.raises(ServiceUnavailableError) as exc:
                    await post_review_pull_request_revision(
                        workspace_id=workspace_id,
                        repository_id=uuid.uuid4(),
                        pull_request_id=uuid.uuid4(),
                        revision_id=uuid.uuid4(),
                        body=ReviewTriggerRequest(),
                        current_user=current_user,
                        session=session,
                        idempotent=None,
                    )
    assert exc.value.error_code == "llm_disabled"


@pytest.mark.asyncio
async def test_get_review_run_returns_judge_fields():
    workspace_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    session = AsyncMock()
    current_user = AsyncMock()
    current_user.workspace_id = workspace_id

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = uuid.uuid4()
    run.created_at = datetime.now(UTC)
    run.updated_at = datetime.now(UTC)
    run.judge_status = GitHubReviewJudgeStatus.skipped_disabled
    run.judge_escalation_candidate_count = 2

    with patch("app.api.v1.workspaces.installation_review.require_permission"):
        with patch("app.api.v1.workspaces.installation_review.require_same_workspace"):
            with patch(
                "app.api.v1.workspaces.installation_review.ensure_revision_access",
                AsyncMock(),
            ):
                with patch(
                    "app.api.v1.workspaces.installation_review.get_latest_review_run",
                    AsyncMock(return_value=run),
                ):
                    response = await get_review_run_for_revision(
                        workspace_id=workspace_id,
                        repository_id=repository_id,
                        pull_request_id=pull_request_id,
                        revision_id=revision_id,
                        current_user=current_user,
                        session=session,
                    )

    assert response.data is not None
    assert response.data.judge_status == GitHubReviewJudgeStatus.skipped_disabled
    assert response.data.judge_escalation_candidate_count == 2
