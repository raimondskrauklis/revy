# backend/tests/unit/test_github_index_routes.py
"""Indexing routes — R3."""
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.api.v1.workspaces.installation_indexing import post_index_pull_request_revision
from app.constants.enums import GitHubIndexJobStatus
from app.core.exceptions import ServiceUnavailableError
from app.models.github_index_job import GitHubIndexJobORM


@pytest.mark.asyncio
async def test_post_index_pull_request_revision_queues_job():
    workspace_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    session = AsyncMock()
    session.commit = AsyncMock()
    current_user = AsyncMock()
    current_user.workspace_id = workspace_id
    current_user.user_id = uuid.uuid4()

    job = GitHubIndexJobORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubIndexJobStatus.pending,
    )
    job.id = uuid.uuid4()
    job.created_at = datetime.now(UTC)
    job.updated_at = datetime.now(UTC)

    with patch("app.api.v1.workspaces.installation_indexing.require_permission"):
        with patch("app.api.v1.workspaces.installation_indexing.require_same_workspace"):
            with patch(
                "app.api.v1.workspaces.installation_indexing.create_index_job",
                AsyncMock(return_value=job),
            ):
                with patch(
                    "app.api.v1.workspaces.installation_indexing.enqueue_index_job",
                ) as enqueue_mock:
                    response = await post_index_pull_request_revision(
                        workspace_id=workspace_id,
                        repository_id=repository_id,
                        pull_request_id=pull_request_id,
                        revision_id=revision_id,
                        current_user=current_user,
                        session=session,
                        idempotent=None,
                    )

    enqueue_mock.assert_called_once_with(job.id)
    assert response.data.status == GitHubIndexJobStatus.pending


@pytest.mark.asyncio
async def test_post_index_disabled_embeddings_raises():
    workspace_id = uuid.uuid4()
    session = AsyncMock()
    current_user = AsyncMock()
    current_user.workspace_id = workspace_id
    current_user.user_id = uuid.uuid4()

    with patch("app.api.v1.workspaces.installation_indexing.require_permission"):
        with patch("app.api.v1.workspaces.installation_indexing.require_same_workspace"):
            with patch(
                "app.api.v1.workspaces.installation_indexing.create_index_job",
                AsyncMock(side_effect=ServiceUnavailableError(
                    message="Embeddings API is not configured",
                    error_code="embeddings_disabled",
                )),
            ):
                with pytest.raises(ServiceUnavailableError) as exc:
                    await post_index_pull_request_revision(
                        workspace_id=workspace_id,
                        repository_id=uuid.uuid4(),
                        pull_request_id=uuid.uuid4(),
                        revision_id=uuid.uuid4(),
                        current_user=current_user,
                        session=session,
                        idempotent=None,
                    )
    assert exc.value.error_code == "embeddings_disabled"
