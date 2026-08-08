# backend/tests/unit/test_github_publish_routes.py
"""Publish routes — R6."""
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.api.v1.workspaces.installation_review import post_publish_pull_request_revision
from app.constants.enums import GitHubPublishJobStatus
from app.models.github_publish_job import GitHubPublishJobORM


@pytest.mark.asyncio
async def test_post_publish_pull_request_revision_queues_job():
    workspace_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    session = AsyncMock()
    session.commit = AsyncMock()
    current_user = AsyncMock()
    current_user.workspace_id = workspace_id
    current_user.user_id = uuid.uuid4()

    job = GitHubPublishJobORM(
        review_run_id=uuid.uuid4(),
        revision_id=revision_id,
        workspace_id=workspace_id,
        head_sha="sha",
        status=GitHubPublishJobStatus.pending,
    )
    job.id = uuid.uuid4()
    job.inline_comments_posted = False
    job.created_at = datetime.now(UTC)
    job.updated_at = datetime.now(UTC)

    with patch("app.api.v1.workspaces.installation_review.require_permission"):
        with patch("app.api.v1.workspaces.installation_review.require_same_workspace"):
            with patch(
                "app.api.v1.workspaces.installation_review.create_publish_job",
                AsyncMock(return_value=job),
            ):
                with patch(
                    "app.api.v1.workspaces.installation_review.enqueue_publish_job",
                ) as enqueue_mock:
                    response = await post_publish_pull_request_revision(
                        workspace_id=workspace_id,
                        repository_id=repository_id,
                        pull_request_id=pull_request_id,
                        revision_id=revision_id,
                        current_user=current_user,
                        session=session,
                        idempotent=None,
                    )

    enqueue_mock.assert_called_once_with(job.id)
    assert response.data.status == GitHubPublishJobStatus.pending


def test_github_publish_job_response_includes_pr_resolution_rollup():
    from app.schemas.github_publish import GitHubPublishJobResponse

    job = GitHubPublishJobORM(
        review_run_id=uuid.uuid4(),
        revision_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        head_sha="sha",
        status=GitHubPublishJobStatus.completed,
    )
    job.id = uuid.uuid4()
    job.inline_comments_posted = False
    job.created_at = datetime.now(UTC)
    job.updated_at = datetime.now(UTC)
    job.summary_json = {
        "pr_resolution_rollup": {
            "schema_version": 1,
            "review_count": 2,
            "raised_count": 3,
            "still_open_display": 1,
        }
    }
    response = GitHubPublishJobResponse.from_publish_job(job)
    assert response.pr_resolution_rollup is not None
    assert response.pr_resolution_rollup["review_count"] == 2
