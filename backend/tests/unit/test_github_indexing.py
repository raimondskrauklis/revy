# backend/tests/unit/test_github_indexing.py
"""GitHub indexing service — R3."""
import uuid
from datetime import UTC, datetime
from pathlib import Path
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.constants.enums import (
    GitHubAccountType,
    GitHubIndexJobStatus,
    GitHubInstallationStatus,
    GitHubPullRequestState,
    GitHubRepositoryStatus,
)
from app.core.exceptions import ServiceUnavailableError
from app.models.github_code_chunk import GitHubCodeChunkORM
from app.models.github_index_job import GitHubIndexJobORM
from app.models.github_installation import GitHubInstallationORM
from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
from app.models.github_repository import GitHubRepositoryORM
from app.services.github_indexing import create_index_job, list_revision_chunks, run_index_job


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
    session.scalar = AsyncMock(return_value=revision_id)
    session.scalars = AsyncMock(return_value=[])

    page = await list_revision_chunks(
        session,
        workspace_id=workspace_id,
        repository_id=repository_id,
        pull_request_id=pull_request_id,
        revision_id=revision_id,
    )
    assert page.items == []
    assert page.has_more is False
    assert page.offset == 0
    assert page.limit == 100


@pytest.mark.asyncio
async def test_list_revision_chunks_sets_has_more_when_paginated():
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

    chunk_one = GitHubCodeChunkORM(
        index_job_id=uuid.uuid4(),
        revision_id=revision_id,
        workspace_id=workspace_id,
        file_path="a.py",
        chunk_index=0,
        content="a",
        embedding=[0.1],
    )
    chunk_one.id = uuid.uuid4()
    chunk_one.created_at = datetime.now(UTC)
    chunk_two = GitHubCodeChunkORM(
        index_job_id=uuid.uuid4(),
        revision_id=revision_id,
        workspace_id=workspace_id,
        file_path="b.py",
        chunk_index=0,
        content="b",
        embedding=[0.2],
    )
    chunk_two.id = uuid.uuid4()
    chunk_two.created_at = datetime.now(UTC)

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=revision_id)
    session.scalars = AsyncMock(return_value=[chunk_one, chunk_two])

    page = await list_revision_chunks(
        session,
        workspace_id=workspace_id,
        repository_id=repository_id,
        pull_request_id=pull_request_id,
        revision_id=revision_id,
        limit=1,
    )

    assert page.has_more is True
    assert len(page.items) == 1


def _index_job_fixture() -> tuple[AsyncMock, GitHubIndexJobORM, GitHubPullRequestRevisionORM]:
    workspace_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    installation_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    job_id = uuid.uuid4()

    job = GitHubIndexJobORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubIndexJobStatus.pending,
    )
    job.id = job_id

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha="sha123",
    )
    revision.id = revision_id

    pull_request = GitHubPullRequestORM(
        repository_id=repository_id,
        workspace_id=workspace_id,
        installation_id=installation_id,
        github_pull_request_id=100,
        number=1,
        title="PR",
        state=GitHubPullRequestState.open,
        head_sha="sha123",
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )
    pull_request.id = pull_request_id

    repository = GitHubRepositoryORM(
        installation_id=installation_id,
        workspace_id=workspace_id,
        github_repository_id=10,
        name="demo",
        full_name="acme/demo",
        private=False,
        status=GitHubRepositoryStatus.active,
    )
    repository.id = repository_id

    installation = GitHubInstallationORM(
        workspace_id=workspace_id,
        github_installation_id=1,
        account_login="acme",
        account_type=GitHubAccountType.organization,
        account_id=2,
        status=GitHubInstallationStatus.active,
    )
    installation.id = installation_id

    session = AsyncMock()

    async def _get(model, pk):
        if pk == job_id:
            return job
        if pk == revision_id:
            return revision
        if pk == pull_request_id:
            return pull_request
        if pk == repository_id:
            return repository
        if pk == installation_id:
            return installation
        return None

    session.get = AsyncMock(side_effect=_get)
    session.flush = AsyncMock()
    session.add = MagicMock()
    session.execute = AsyncMock()

    return session, job, revision


@pytest.mark.asyncio
async def test_run_index_job_skips_non_pending_status():
    session, job, _revision = _index_job_fixture()
    job.status = GitHubIndexJobStatus.processing

    with patch("app.services.github_indexing.download_repository_tarball", AsyncMock()) as download_mock:
        result = await run_index_job(session, index_job_id=job.id)

    assert result.status == GitHubIndexJobStatus.processing
    download_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_index_job_preserves_chunks_when_embed_fails():
    session, job, revision = _index_job_fixture()

    with patch("app.services.github_indexing.settings") as mock_settings:
        mock_settings.revy_worktrees_path = "/tmp/revy-worktrees"
        with patch("app.services.github_indexing.download_repository_tarball", AsyncMock(return_value=b"archive")):
            with patch("app.services.github_indexing.extract_tarball", return_value=Path("/tmp/revy-worktrees") / str(revision.id)):
                with patch(
                    "app.services.github_indexing.iter_indexable_files",
                    return_value=[("main.py", "print('hi')")],
                ):
                    with patch(
                        "app.services.github_indexing.chunk_file_content",
                        return_value=[MagicMock(file_path="main.py", chunk_index=0, content="print('hi')")],
                    ):
                        with patch(
                            "app.services.github_indexing.embed_texts",
                            AsyncMock(side_effect=httpx.HTTPError("embed failed")),
                        ):
                            with patch("pathlib.Path.exists", return_value=False):
                                result = await run_index_job(session, index_job_id=job.id)

    assert result.status == GitHubIndexJobStatus.failed
    session.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_index_job_resets_pending_on_rate_limit():
    session, job, revision = _index_job_fixture()
    response = MagicMock()
    response.status_code = 429
    rate_limit_error = httpx.HTTPStatusError(
        "Too Many Requests",
        request=MagicMock(),
        response=response,
    )

    with patch("app.services.github_indexing.settings") as mock_settings:
        mock_settings.revy_worktrees_path = "/tmp/revy-worktrees"
        with patch("app.services.github_indexing.download_repository_tarball", AsyncMock(return_value=b"archive")):
            with patch("app.services.github_indexing.extract_tarball", return_value=Path("/tmp/revy-worktrees") / str(revision.id)):
                with patch(
                    "app.services.github_indexing.iter_indexable_files",
                    return_value=[("main.py", "print('hi')")],
                ):
                    with patch(
                        "app.services.github_indexing.chunk_file_content",
                        return_value=[MagicMock(file_path="main.py", chunk_index=0, content="print('hi')")],
                    ):
                        with patch(
                            "app.services.github_indexing.embed_texts",
                            AsyncMock(side_effect=rate_limit_error),
                        ):
                            with patch("pathlib.Path.exists", return_value=False):
                                with pytest.raises(httpx.HTTPStatusError):
                                    await run_index_job(session, index_job_id=job.id)

    assert job.status == GitHubIndexJobStatus.pending
    assert job.error_message is None
    session.execute.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_index_job_deletes_chunks_after_embed_success():
    session, job, revision = _index_job_fixture()

    with patch("app.services.github_indexing.settings") as mock_settings:
        mock_settings.revy_worktrees_path = "/tmp/revy-worktrees"
        with patch("app.services.github_indexing.download_repository_tarball", AsyncMock(return_value=b"archive")):
            with patch("app.services.github_indexing.extract_tarball", return_value=Path("/tmp/revy-worktrees") / str(revision.id)):
                with patch(
                    "app.services.github_indexing.iter_indexable_files",
                    return_value=[("main.py", "print('hi')")],
                ):
                    with patch(
                        "app.services.github_indexing.chunk_file_content",
                        return_value=[MagicMock(file_path="main.py", chunk_index=0, content="print('hi')")],
                    ):
                        with patch(
                            "app.services.github_indexing.embed_texts",
                            AsyncMock(return_value=[[0.1, 0.2]]),
                        ):
                            with patch("pathlib.Path.exists", return_value=False):
                                result = await run_index_job(session, index_job_id=job.id)

    assert result.status == GitHubIndexJobStatus.completed
    session.execute.assert_awaited_once()
    session.add.assert_called_once()
