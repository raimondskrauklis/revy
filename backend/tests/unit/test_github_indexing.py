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
    GitHubIndexMode,
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
    session.scalar = AsyncMock(return_value=1)

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
    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_run_index_job_marks_failed_on_rate_limit():
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
                                result = await run_index_job(session, index_job_id=job.id)

    assert result.status == GitHubIndexJobStatus.failed
    assert result.error_message is not None
    session.add.assert_not_called()


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
    session.execute.assert_awaited()
    session.add.assert_called_once()


@pytest.mark.asyncio
async def test_hash_chunk_content_is_stable():
    from app.services.github_indexing import _hash_chunk_content

    assert _hash_chunk_content("print('hi')") == _hash_chunk_content("print('hi')")
    assert _hash_chunk_content("a") != _hash_chunk_content("b")


@pytest.mark.asyncio
async def test_get_parent_revision_returns_none_for_first_push():
    from app.services.github_indexing import _get_parent_revision

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=uuid.uuid4(),
        revision_number=1,
        head_sha="sha",
    )
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)

    parent = await _get_parent_revision(session, revision)

    assert parent is None
    session.scalar.assert_not_awaited()


@pytest.mark.asyncio
async def test_run_index_job_reuses_matching_parent_chunks():
    session, job, revision = _index_job_fixture()
    revision.revision_number = 2
    revision.base_sha = "base"
    job.index_incremental = True
    job.index_mode = GitHubIndexMode.diff

    parent_chunk = GitHubCodeChunkORM(
        index_job_id=uuid.uuid4(),
        revision_id=uuid.uuid4(),
        workspace_id=job.workspace_id,
        file_path="main.py",
        chunk_index=0,
        content="print('hi')",
        content_hash=None,
        embedding=[0.1, 0.2],
    )
    parent_revision = GitHubPullRequestRevisionORM(
        pull_request_id=revision.pull_request_id,
        revision_number=1,
        head_sha="old",
    )
    parent_revision.id = uuid.uuid4()

    compare_result = MagicMock()
    compare_result.paths_to_index = {"main.py"}
    compare_result.paths_to_remove = []

    with patch("app.services.github_indexing.settings") as mock_settings:
        mock_settings.revy_worktrees_path = "/tmp/revy-worktrees"
        with patch("app.services.github_indexing._get_parent_revision", AsyncMock(return_value=parent_revision)):
            with patch(
                "app.services.github_indexing._load_parent_chunks",
                AsyncMock(return_value={(parent_chunk.file_path, parent_chunk.chunk_index): parent_chunk}),
            ):
                with patch("app.services.github_indexing.compare_commits", AsyncMock(return_value=compare_result)):
                    with patch("app.services.github_indexing.download_repository_tarball", AsyncMock(return_value=b"archive")):
                        with patch(
                            "app.services.github_indexing.extract_tarball",
                            return_value=Path("/tmp/revy-worktrees") / str(revision.id),
                        ):
                            with patch(
                                "app.services.github_indexing.iter_indexable_files",
                                return_value=[("main.py", "print('hi')")],
                            ):
                                with patch(
                                    "app.services.github_indexing.chunk_file_content",
                                    return_value=[MagicMock(file_path="main.py", chunk_index=0, content="print('hi')")],
                                ):
                                    with patch("app.services.github_indexing.embed_texts", AsyncMock()) as embed_mock:
                                        with patch("pathlib.Path.exists", return_value=False):
                                            result = await run_index_job(session, index_job_id=job.id)

    assert result.status == GitHubIndexJobStatus.completed
    embed_mock.assert_not_awaited()
    assert result.index_manifest_stats["reused_count"] == 1
    assert result.index_manifest_stats["new_count"] == 0
    assert result.index_manifest_stats["embed_batches"] == 0
    added_chunk = session.add.call_args.args[0]
    assert added_chunk.content_hash is not None
    assert added_chunk.embedding == [0.1, 0.2]


@pytest.mark.asyncio
async def test_run_index_job_reembeds_when_content_changes():
    session, job, revision = _index_job_fixture()
    revision.revision_number = 2
    revision.base_sha = "base"
    job.index_incremental = True
    job.index_mode = GitHubIndexMode.diff

    parent_chunk = GitHubCodeChunkORM(
        index_job_id=uuid.uuid4(),
        revision_id=uuid.uuid4(),
        workspace_id=job.workspace_id,
        file_path="main.py",
        chunk_index=0,
        content="print('old')",
        content_hash=None,
        embedding=[0.1, 0.2],
    )
    parent_revision = GitHubPullRequestRevisionORM(
        pull_request_id=revision.pull_request_id,
        revision_number=1,
        head_sha="old",
    )
    parent_revision.id = uuid.uuid4()

    compare_result = MagicMock()
    compare_result.paths_to_index = {"main.py"}
    compare_result.paths_to_remove = []

    with patch("app.services.github_indexing.settings") as mock_settings:
        mock_settings.revy_worktrees_path = "/tmp/revy-worktrees"
        with patch("app.services.github_indexing._get_parent_revision", AsyncMock(return_value=parent_revision)):
            with patch(
                "app.services.github_indexing._load_parent_chunks",
                AsyncMock(return_value={(parent_chunk.file_path, parent_chunk.chunk_index): parent_chunk}),
            ):
                with patch("app.services.github_indexing.compare_commits", AsyncMock(return_value=compare_result)):
                    with patch("app.services.github_indexing.download_repository_tarball", AsyncMock(return_value=b"archive")):
                        with patch(
                            "app.services.github_indexing.extract_tarball",
                            return_value=Path("/tmp/revy-worktrees") / str(revision.id),
                        ):
                            with patch(
                                "app.services.github_indexing.iter_indexable_files",
                                return_value=[("main.py", "print('new')")],
                            ):
                                with patch(
                                    "app.services.github_indexing.chunk_file_content",
                                    return_value=[MagicMock(file_path="main.py", chunk_index=0, content="print('new')")],
                                ):
                                    with patch(
                                        "app.services.github_indexing.embed_texts",
                                        AsyncMock(return_value=[[0.3, 0.4]]),
                                    ) as embed_mock:
                                        with patch("pathlib.Path.exists", return_value=False):
                                            result = await run_index_job(session, index_job_id=job.id)

    assert result.status == GitHubIndexJobStatus.completed
    embed_mock.assert_awaited_once()
    assert result.index_manifest_stats["new_count"] == 1
    added_chunk = session.add.call_args.args[0]
    assert added_chunk.embedding == [0.3, 0.4]


@pytest.mark.asyncio
async def test_run_index_job_copy_forwards_unchanged_paths_on_diff():
    session, job, revision = _index_job_fixture()
    revision.revision_number = 2
    revision.base_sha = "base"
    job.index_incremental = True
    job.index_mode = GitHubIndexMode.diff

    parent_chunk = GitHubCodeChunkORM(
        index_job_id=uuid.uuid4(),
        revision_id=uuid.uuid4(),
        workspace_id=job.workspace_id,
        file_path="stable.py",
        chunk_index=0,
        content="stable",
        content_hash="abc",
        embedding=[0.5],
    )
    parent_revision = GitHubPullRequestRevisionORM(
        pull_request_id=revision.pull_request_id,
        revision_number=1,
        head_sha="old",
    )
    parent_revision.id = uuid.uuid4()

    compare_result = MagicMock()
    compare_result.paths_to_index = {"changed.py"}
    compare_result.paths_to_remove = ["removed.py"]

    with patch("app.services.github_indexing.settings") as mock_settings:
        mock_settings.revy_worktrees_path = "/tmp/revy-worktrees"
        with patch("app.services.github_indexing._get_parent_revision", AsyncMock(return_value=parent_revision)):
            with patch(
                "app.services.github_indexing._load_parent_chunks",
                AsyncMock(return_value={(parent_chunk.file_path, parent_chunk.chunk_index): parent_chunk}),
            ):
                with patch("app.services.github_indexing.compare_commits", AsyncMock(return_value=compare_result)):
                    with patch("app.services.github_indexing.download_repository_tarball", AsyncMock(return_value=b"archive")):
                        with patch(
                            "app.services.github_indexing.extract_tarball",
                            return_value=Path("/tmp/revy-worktrees") / str(revision.id),
                        ):
                            with patch(
                                "app.services.github_indexing.iter_indexable_files",
                                return_value=[("changed.py", "new")],
                            ):
                                with patch(
                                    "app.services.github_indexing.chunk_file_content",
                                    return_value=[MagicMock(file_path="changed.py", chunk_index=0, content="new")],
                                ):
                                    with patch(
                                        "app.services.github_indexing.embed_texts",
                                        AsyncMock(return_value=[[0.9]]),
                                    ):
                                        with patch("pathlib.Path.exists", return_value=False):
                                            result = await run_index_job(session, index_job_id=job.id)

    assert result.status == GitHubIndexJobStatus.completed
    assert result.index_manifest_stats["reused_count"] == 1
    assert result.index_manifest_stats["new_count"] == 1
    file_paths = {call.args[0].file_path for call in session.add.call_args_list}
    assert file_paths == {"stable.py", "changed.py"}


@pytest.mark.asyncio
async def test_run_index_job_copy_forwards_on_deletion_only_synchronize():
    session, job, revision = _index_job_fixture()
    revision.revision_number = 2
    revision.base_sha = "base"
    job.index_incremental = True
    job.index_mode = GitHubIndexMode.diff

    parent_chunk = GitHubCodeChunkORM(
        index_job_id=uuid.uuid4(),
        revision_id=uuid.uuid4(),
        workspace_id=job.workspace_id,
        file_path="stable.py",
        chunk_index=0,
        content="stable",
        content_hash="abc",
        embedding=[0.5],
    )
    parent_revision = GitHubPullRequestRevisionORM(
        pull_request_id=revision.pull_request_id,
        revision_number=1,
        head_sha="old",
    )
    parent_revision.id = uuid.uuid4()

    compare_result = MagicMock()
    compare_result.paths_to_index = set()
    compare_result.paths_to_remove = ["removed.py"]

    with patch("app.services.github_indexing.settings") as mock_settings:
        mock_settings.revy_worktrees_path = "/tmp/revy-worktrees"
        with patch("app.services.github_indexing._get_parent_revision", AsyncMock(return_value=parent_revision)):
            with patch(
                "app.services.github_indexing._load_parent_chunks",
                AsyncMock(return_value={(parent_chunk.file_path, parent_chunk.chunk_index): parent_chunk}),
            ):
                with patch("app.services.github_indexing.compare_commits", AsyncMock(return_value=compare_result)):
                    with patch("app.services.github_indexing.download_repository_tarball", AsyncMock(return_value=b"archive")):
                        with patch(
                            "app.services.github_indexing.extract_tarball",
                            return_value=Path("/tmp/revy-worktrees") / str(revision.id),
                        ):
                            with patch(
                                "app.services.github_indexing.iter_indexable_files",
                                return_value=[],
                            ):
                                with patch("app.services.github_indexing.embed_texts", AsyncMock()) as embed_mock:
                                    with patch("pathlib.Path.exists", return_value=False):
                                        result = await run_index_job(session, index_job_id=job.id)

    assert result.status == GitHubIndexJobStatus.completed
    embed_mock.assert_not_awaited()
    assert result.index_manifest_stats["reused_count"] == 1
    assert result.index_manifest_stats["new_count"] == 0
    added_chunk = session.add.call_args.args[0]
    assert added_chunk.file_path == "stable.py"


@pytest.mark.asyncio
async def test_run_index_job_rolls_back_chunks_when_embed_fails_after_copy_forward():
    session, job, revision = _index_job_fixture()
    revision.revision_number = 2
    revision.base_sha = "base"
    job.index_incremental = True
    job.index_mode = GitHubIndexMode.diff

    parent_chunk = GitHubCodeChunkORM(
        index_job_id=uuid.uuid4(),
        revision_id=uuid.uuid4(),
        workspace_id=job.workspace_id,
        file_path="stable.py",
        chunk_index=0,
        content="stable",
        content_hash="abc",
        embedding=[0.5],
    )
    parent_revision = GitHubPullRequestRevisionORM(
        pull_request_id=revision.pull_request_id,
        revision_number=1,
        head_sha="old",
    )
    parent_revision.id = uuid.uuid4()

    compare_result = MagicMock()
    compare_result.paths_to_index = {"changed.py"}
    compare_result.paths_to_remove = []

    session.rollback = AsyncMock()

    with patch("app.services.github_indexing.settings") as mock_settings:
        mock_settings.revy_worktrees_path = "/tmp/revy-worktrees"
        with patch("app.services.github_indexing._get_parent_revision", AsyncMock(return_value=parent_revision)):
            with patch(
                "app.services.github_indexing._load_parent_chunks",
                AsyncMock(return_value={(parent_chunk.file_path, parent_chunk.chunk_index): parent_chunk}),
            ):
                with patch("app.services.github_indexing.compare_commits", AsyncMock(return_value=compare_result)):
                    with patch("app.services.github_indexing.download_repository_tarball", AsyncMock(return_value=b"archive")):
                        with patch(
                            "app.services.github_indexing.extract_tarball",
                            return_value=Path("/tmp/revy-worktrees") / str(revision.id),
                        ):
                            with patch(
                                "app.services.github_indexing.iter_indexable_files",
                                return_value=[("changed.py", "new")],
                            ):
                                with patch(
                                    "app.services.github_indexing.chunk_file_content",
                                    return_value=[MagicMock(file_path="changed.py", chunk_index=0, content="new")],
                                ):
                                    with patch(
                                        "app.services.github_indexing.embed_texts",
                                        AsyncMock(side_effect=httpx.HTTPError("embed failed")),
                                    ):
                                        with patch("pathlib.Path.exists", return_value=False):
                                            result = await run_index_job(session, index_job_id=job.id)

    assert result.status == GitHubIndexJobStatus.failed
    session.rollback.assert_awaited_once()
