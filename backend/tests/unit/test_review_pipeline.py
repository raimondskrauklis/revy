# backend/tests/unit/test_review_pipeline.py
"""Review pipeline orchestration — R8."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.constants.enums import (
    GitHubIndexJobStatus,
    GitHubIndexJobTriggerSource,
    GitHubPullRequestState,
    WorkspaceStatus,
)
from app.core.exceptions import ConflictError
from app.models.github_index_job import GitHubIndexJobORM
from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
from app.models.workspaces import WorkspaceORM
from app.services.review_pipeline import (
    maybe_enqueue_pipeline_for_revision,
    prepare_review_after_index,
)


def _workspace(*, autostart: bool = True) -> WorkspaceORM:
    workspace = WorkspaceORM(
        slug="acme",
        name="Acme",
        status=WorkspaceStatus.active,
        review_autostart_enabled=autostart,
    )
    workspace.id = uuid.uuid4()
    return workspace


def _revision_chain(
    workspace_id: uuid.UUID,
    *,
    is_draft: bool = False,
    state: GitHubPullRequestState = GitHubPullRequestState.open,
) -> tuple[GitHubPullRequestRevisionORM, GitHubPullRequestORM]:
    pull_request = GitHubPullRequestORM(
        repository_id=uuid.uuid4(),
        workspace_id=workspace_id,
        installation_id=uuid.uuid4(),
        github_pull_request_id=1,
        number=1,
        title="PR",
        state=state,
        head_sha="sha",
        head_ref="feature",
        base_ref="main",
        revision_count=1,
        is_draft=is_draft,
    )
    pull_request.id = uuid.uuid4()
    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request.id,
        revision_number=1,
        head_sha="sha",
    )
    revision.id = uuid.uuid4()
    return revision, pull_request


@pytest.mark.asyncio
async def test_maybe_enqueue_pipeline_skips_draft_pull_request():
    workspace = _workspace()
    revision, pull_request = _revision_chain(workspace.id, is_draft=True)
    session = AsyncMock()
    session.get = AsyncMock(side_effect=[revision, pull_request, workspace])

    with patch("app.services.review_pipeline.pipeline_prerequisites_met", return_value=True):
        job_id = await maybe_enqueue_pipeline_for_revision(
            session,
            workspace_id=workspace.id,
            revision_id=revision.id,
            trigger=GitHubIndexJobTriggerSource.autostart,
        )

    assert job_id is None
    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_maybe_enqueue_pipeline_skips_closed_pull_request():
    workspace = _workspace()
    revision, pull_request = _revision_chain(
        workspace.id,
        state=GitHubPullRequestState.closed,
    )
    session = AsyncMock()
    session.get = AsyncMock(side_effect=[revision, pull_request])

    with patch("app.services.review_pipeline.pipeline_prerequisites_met", return_value=True):
        job_id = await maybe_enqueue_pipeline_for_revision(
            session,
            workspace_id=workspace.id,
            revision_id=revision.id,
            trigger=GitHubIndexJobTriggerSource.autostart,
        )

    assert job_id is None
    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_maybe_enqueue_pipeline_creates_index_job():
    workspace = _workspace()
    revision, pull_request = _revision_chain(workspace.id)
    session = AsyncMock()
    session.get = AsyncMock(side_effect=[revision, pull_request, workspace])
    session.scalar = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.flush = AsyncMock()

    with patch("app.services.review_pipeline.pipeline_prerequisites_met", return_value=True):
        job_id = await maybe_enqueue_pipeline_for_revision(
            session,
            workspace_id=workspace.id,
            revision_id=revision.id,
            trigger=GitHubIndexJobTriggerSource.autostart,
        )

    assert job_id is not None or session.add.called
    session.add.assert_called_once()
    added = session.add.call_args.args[0]
    assert added.trigger_source == GitHubIndexJobTriggerSource.autostart


@pytest.mark.asyncio
async def test_maybe_enqueue_pipeline_skips_when_autostart_disabled():
    workspace = _workspace(autostart=False)
    revision, pull_request = _revision_chain(workspace.id)
    session = AsyncMock()
    session.get = AsyncMock(side_effect=[revision, pull_request, workspace])

    with patch("app.services.review_pipeline.pipeline_prerequisites_met", return_value=True):
        job_id = await maybe_enqueue_pipeline_for_revision(
            session,
            workspace_id=workspace.id,
            revision_id=revision.id,
            trigger=GitHubIndexJobTriggerSource.autostart,
        )

    assert job_id is None
    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_maybe_enqueue_pipeline_command_ignores_autostart_flag():
    workspace = _workspace(autostart=False)
    revision, pull_request = _revision_chain(workspace.id)
    session = AsyncMock()
    session.get = AsyncMock(side_effect=[revision, pull_request, workspace])
    session.scalar = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.flush = AsyncMock()

    with patch("app.services.review_pipeline.pipeline_prerequisites_met", return_value=True):
        job_id = await maybe_enqueue_pipeline_for_revision(
            session,
            workspace_id=workspace.id,
            revision_id=revision.id,
            trigger=GitHubIndexJobTriggerSource.command,
        )

    assert job_id is not None or session.add.called


@pytest.mark.asyncio
async def test_maybe_enqueue_pipeline_skips_when_index_job_pending():
    workspace = _workspace()
    revision, pull_request = _revision_chain(workspace.id)
    session = AsyncMock()
    session.get = AsyncMock(side_effect=[revision, pull_request, workspace])
    session.scalar = AsyncMock(return_value=uuid.uuid4())

    with patch("app.services.review_pipeline.pipeline_prerequisites_met", return_value=True):
        with patch(
            "app.services.review_pipeline.index_job_in_progress",
            AsyncMock(return_value=True),
        ):
            job_id = await maybe_enqueue_pipeline_for_revision(
                session,
                workspace_id=workspace.id,
                revision_id=revision.id,
                trigger=GitHubIndexJobTriggerSource.autostart,
            )

    assert job_id is None
    session.add.assert_not_called()


@pytest.mark.asyncio
@patch("app.services.review_pipeline.create_review_run", new_callable=AsyncMock)
async def test_prepare_review_after_index_reuses_pending_review(create_review_run_mock: AsyncMock):
    workspace_id = uuid.uuid4()
    pending_review_id = uuid.uuid4()
    job = GitHubIndexJobORM(
        revision_id=uuid.uuid4(),
        workspace_id=workspace_id,
        status=GitHubIndexJobStatus.completed,
        trigger_source=GitHubIndexJobTriggerSource.command,
    )
    session = AsyncMock()
    session.get = AsyncMock()
    session.scalar = AsyncMock(return_value=pending_review_id)

    result = await prepare_review_after_index(session, job)

    assert result == pending_review_id
    create_review_run_mock.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.services.review_pipeline.create_review_run", new_callable=AsyncMock)
async def test_prepare_review_after_index_for_autostart(create_review_run_mock: AsyncMock):
    workspace_id = uuid.uuid4()
    revision, pull_request = _revision_chain(workspace_id)
    job = GitHubIndexJobORM(
        revision_id=revision.id,
        workspace_id=workspace_id,
        status=GitHubIndexJobStatus.completed,
        trigger_source=GitHubIndexJobTriggerSource.autostart,
    )
    job.id = uuid.uuid4()
    review_run_id = uuid.uuid4()
    create_review_run_mock.return_value = type("Run", (), {"id": review_run_id})()

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[revision, pull_request])
    session.scalar = AsyncMock(return_value=None)

    result = await prepare_review_after_index(session, job)

    assert result == review_run_id
    create_review_run_mock.assert_awaited_once()


@pytest.mark.asyncio
@patch("app.services.review_pipeline.create_review_run", new_callable=AsyncMock)
async def test_prepare_review_after_index_skips_draft_pull_request(create_review_run_mock: AsyncMock):
    workspace_id = uuid.uuid4()
    revision, pull_request = _revision_chain(workspace_id, is_draft=True)
    job = GitHubIndexJobORM(
        revision_id=revision.id,
        workspace_id=workspace_id,
        status=GitHubIndexJobStatus.completed,
        trigger_source=GitHubIndexJobTriggerSource.autostart,
    )
    job.id = uuid.uuid4()

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[revision, pull_request])
    session.scalar = AsyncMock(return_value=None)

    assert await prepare_review_after_index(session, job) is None
    create_review_run_mock.assert_not_awaited()


@pytest.mark.asyncio
@patch("app.services.review_pipeline.create_review_run", new_callable=AsyncMock)
async def test_prepare_review_after_index_skips_closed_pull_request(create_review_run_mock: AsyncMock):
    workspace_id = uuid.uuid4()
    revision, pull_request = _revision_chain(
        workspace_id,
        state=GitHubPullRequestState.closed,
    )
    job = GitHubIndexJobORM(
        revision_id=revision.id,
        workspace_id=workspace_id,
        status=GitHubIndexJobStatus.completed,
        trigger_source=GitHubIndexJobTriggerSource.command,
    )
    job.id = uuid.uuid4()

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[revision, pull_request])
    session.scalar = AsyncMock(return_value=None)

    assert await prepare_review_after_index(session, job) is None
    create_review_run_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_prepare_review_after_index_skips_manual_trigger():
    job = GitHubIndexJobORM(
        revision_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        status=GitHubIndexJobStatus.completed,
        trigger_source=GitHubIndexJobTriggerSource.manual,
    )
    session = AsyncMock()

    assert await prepare_review_after_index(session, job) is None


@pytest.mark.asyncio
async def test_create_index_job_raises_index_in_progress():
    from app.services.github_indexing import create_index_job

    session = AsyncMock()

    with patch("app.services.github_indexing.settings") as mock_settings:
        mock_settings.embeddings_enabled = True
        mock_settings.github_api_enabled = True
        with patch(
            "app.services.github_indexing.ensure_revision_access",
            AsyncMock(),
        ):
            with patch(
                "app.services.github_indexing.index_job_in_progress",
                AsyncMock(return_value=True),
            ):
                with pytest.raises(ConflictError) as exc:
                    await create_index_job(
                        session,
                        workspace_id=uuid.uuid4(),
                        repository_id=uuid.uuid4(),
                        pull_request_id=uuid.uuid4(),
                        revision_id=uuid.uuid4(),
                    )

    assert exc.value.error_code == "index_in_progress"
