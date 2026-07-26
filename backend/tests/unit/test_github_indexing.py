# backend/tests/unit/test_github_indexing.py
"""GitHub indexing service — R3."""
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.constants.enums import (
    GitHubAccountType,
    GitHubInstallationStatus,
    GitHubPullRequestState,
    GitHubRepositoryStatus,
)
from app.core.exceptions import ServiceUnavailableError
from app.models.github_installation import GitHubInstallationORM
from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
from app.models.github_repository import GitHubRepositoryORM
from app.services.github_indexing import create_index_job, list_revision_chunks


@pytest.mark.asyncio
async def test_create_index_job_disabled_embeddings_raises():
    session = AsyncMock()
    with patch("app.services.github_indexing.settings") as mock_settings:
        mock_settings.embeddings_enabled = False
        with pytest.raises(ServiceUnavailableError) as exc:
            await create_index_job(
                session,
                workspace_id=uuid.uuid4(),
                repository_id=uuid.uuid4(),
                pull_request_id=uuid.uuid4(),
                revision_id=uuid.uuid4(),
            )
    assert exc.value.error_code == "embeddings_disabled"


@pytest.mark.asyncio
async def test_list_revision_chunks_returns_rows():
    workspace_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    revision_id = uuid.uuid4()

    installation = GitHubInstallationORM(
        workspace_id=workspace_id,
        github_installation_id=1,
        account_login="acme",
        account_type=GitHubAccountType.organization,
        account_id=2,
        status=GitHubInstallationStatus.active,
    )
    installation.id = uuid.uuid4()

    repository = GitHubRepositoryORM(
        installation_id=installation.id,
        workspace_id=workspace_id,
        github_repository_id=10,
        name="demo",
        full_name="acme/demo",
        private=False,
        status=GitHubRepositoryStatus.active,
    )
    repository.id = repository_id

    pull_request = GitHubPullRequestORM(
        repository_id=repository_id,
        workspace_id=workspace_id,
        installation_id=installation.id,
        github_pull_request_id=100,
        number=1,
        title="PR",
        state=GitHubPullRequestState.open,
        head_sha="sha",
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )
    pull_request.id = pull_request_id

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha="sha",
    )
    revision.id = revision_id

    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[revision, pull_request, repository, installation])
    session.scalars = AsyncMock(return_value=[])

    chunks = await list_revision_chunks(
        session,
        workspace_id=workspace_id,
        repository_id=repository_id,
        pull_request_id=pull_request_id,
        revision_id=revision_id,
    )
    assert chunks == []
