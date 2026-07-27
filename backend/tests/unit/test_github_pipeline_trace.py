# backend/tests/unit/test_github_pipeline_trace.py
"""GitHub pipeline trace service — review-quality RQ3."""
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.constants.enums import (
    GitHubAccountType,
    GitHubIndexJobStatus,
    GitHubIndexMode,
    GitHubPullRequestState,
    GitHubRepositoryStatus,
    GitHubReviewRunStatus,
    PipelineArtifactKind,
    PipelineStepStatus,
    PipelineStepType,
    ReviewProfile,
)
from app.core.config import settings
from app.models.github_index_job import GitHubIndexJobORM
from app.models.github_installation import GitHubInstallationORM
from app.models.github_pipeline import (
    GitHubPipelineArtifactORM,
    GitHubPipelineRunORM,
    GitHubPipelineStepORM,
)
from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
from app.models.github_repository import GitHubRepositoryORM
from app.models.github_review_run import GitHubReviewRunORM
from app.services.github_pipeline_trace import (
    ensure_pipeline_run_for_index_job,
    finalize_pipeline_github_check_neutral,
    get_pipeline_trace_for_review_run,
    purge_old_pipeline_artifacts,
    record_index_pipeline_step,
    record_review_pipeline_step,
    start_pipeline_github_check,
)


@pytest.mark.asyncio
async def test_ensure_pipeline_run_for_index_job_creates_once():
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    job = GitHubIndexJobORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubIndexJobStatus.pending,
        index_mode=GitHubIndexMode.diff,
    )
    job.id = uuid.uuid4()

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.flush = AsyncMock()

    first = await ensure_pipeline_run_for_index_job(session, job=job, head_sha="abc")
    session.scalar = AsyncMock(return_value=first)
    second = await ensure_pipeline_run_for_index_job(session, job=job, head_sha="abc")

    assert first is second or first.id == second.id
    assert session.add.call_count == 1


@pytest.mark.asyncio
async def test_record_index_pipeline_step_writes_manifest():
    pipeline_run_id = uuid.uuid4()
    job = GitHubIndexJobORM(
        revision_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        status=GitHubIndexJobStatus.completed,
        index_mode=GitHubIndexMode.diff,
        chunk_count=12,
        fallback_reason="missing_base_sha",
    )
    job.id = uuid.uuid4()

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.flush = AsyncMock()

    await record_index_pipeline_step(
        session,
        pipeline_run_id=pipeline_run_id,
        job=job,
        duration_ms=1500,
        github_check_run_id=99,
    )

    assert session.add.call_count >= 2


@pytest.mark.asyncio
async def test_record_review_pipeline_step_stores_prompt_and_parse_report():
    pipeline_run_id = uuid.uuid4()
    run = GitHubReviewRunORM(
        revision_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
        model_id="kimi-k2.7-code",
    )
    run.id = uuid.uuid4()

    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()

    await record_review_pipeline_step(
        session,
        pipeline_run_id=pipeline_run_id,
        run=run,
        prompt="review prompt",
        raw_response='{"findings":[]}',
        parse_report={"parsed_count": 0, "dropped_count": 0, "drop_reasons": {}},
        duration_ms=900,
    )

    assert session.add.call_count >= 3


@pytest.mark.asyncio
async def test_get_pipeline_trace_for_review_run_returns_steps():
    workspace_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    review_run_id = uuid.uuid4()
    pipeline_run_id = uuid.uuid4()
    step_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    pipeline_run = GitHubPipelineRunORM(
        workspace_id=workspace_id,
        revision_id=revision_id,
        head_sha="abc",
        index_mode=GitHubIndexMode.diff,
        review_run_id=review_run_id,
    )
    pipeline_run.id = pipeline_run_id
    pipeline_run.created_at = datetime.now(UTC)
    pipeline_run.updated_at = datetime.now(UTC)

    step = GitHubPipelineStepORM(
        pipeline_run_id=pipeline_run_id,
        step_type=PipelineStepType.review,
        status=PipelineStepStatus.completed,
        duration_ms=100,
    )
    step.id = step_id
    step.created_at = datetime.now(UTC)
    step.updated_at = datetime.now(UTC)
    step.artifacts = [
        GitHubPipelineArtifactORM(
            step_id=step_id,
            kind=PipelineArtifactKind.prompt,
            content_text="prompt body",
        )
    ]
    step.artifacts[0].id = uuid.uuid4()
    step.artifacts[0].created_at = datetime.now(UTC)
    pipeline_run.steps = [step]

    session = AsyncMock()
    session.get = AsyncMock(return_value=run)
    session.scalar = AsyncMock(return_value=pipeline_run)

    with patch(
        "app.services.github_pipeline_trace.ensure_revision_access",
        AsyncMock(),
    ):
        response = await get_pipeline_trace_for_review_run(
            session,
            workspace_id=workspace_id,
            repository_id=repository_id,
            pull_request_id=pull_request_id,
            revision_id=revision_id,
            review_run_id=review_run_id,
        )

    assert response.id == pipeline_run_id
    assert len(response.steps) == 1
    assert response.steps[0].step_type == PipelineStepType.review
    assert response.steps[0].artifacts[0].kind == PipelineArtifactKind.prompt


@pytest.mark.asyncio
async def test_purge_old_pipeline_artifacts_deletes_rows():
    session = AsyncMock()
    result = MagicMock()
    result.rowcount = 3
    session.execute = AsyncMock(return_value=result)

    deleted = await purge_old_pipeline_artifacts(session)

    assert deleted == 3
    assert settings.pipeline_retention_days == 90


@pytest.mark.asyncio
async def test_finalize_pipeline_github_check_neutral_updates_check():
    pipeline_run_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    installation_id = uuid.uuid4()

    pipeline_run = MagicMock()
    pipeline_run.revision_id = revision_id

    revision = MagicMock()
    revision.pull_request_id = pull_request_id

    pull_request = MagicMock()
    pull_request.repository_id = repository_id
    pull_request.installation_id = installation_id

    repository = MagicMock()
    repository.full_name = "owner/repo"

    installation = MagicMock()
    installation.github_installation_id = 12345

    session = AsyncMock()
    session.get = AsyncMock(
        side_effect=[pipeline_run, revision, pull_request, repository, installation]
    )

    with patch(
        "app.services.github_pipeline_trace.resolve_pipeline_github_check_run_id",
        AsyncMock(return_value=42),
    ):
        with patch("app.services.github_pipeline_trace.settings") as mock_settings:
            mock_settings.github_api_enabled = True
            with patch(
                "app.services.github_pipeline_trace.github_api.update_check_run",
                AsyncMock(),
            ) as update_mock:
                with patch("app.services.github_pipeline_trace.httpx.AsyncClient") as client_mock:
                    client = AsyncMock()
                    client.__aenter__ = AsyncMock(return_value=client)
                    client.__aexit__ = AsyncMock(return_value=None)
                    client_mock.return_value = client

                    await finalize_pipeline_github_check_neutral(
                        session,
                        pipeline_run_id=pipeline_run_id,
                        summary="Review skipped — pull request is draft or not open",
                    )

    update_mock.assert_awaited_once()
    assert update_mock.await_args.kwargs["conclusion"] == "neutral"
    assert update_mock.await_args.kwargs["check_run_id"] == 42


@pytest.mark.asyncio
async def test_start_pipeline_github_check_creates_in_progress_run():
    workspace_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    installation_id = uuid.uuid4()
    revision_id = uuid.uuid4()

    pipeline_run = GitHubPipelineRunORM(
        workspace_id=workspace_id,
        revision_id=revision_id,
        head_sha="abc123",
        index_mode=GitHubIndexMode.diff,
    )
    pipeline_run.id = uuid.uuid4()

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha="abc123",
    )
    revision.id = revision_id

    pull_request = GitHubPullRequestORM(
        repository_id=repository_id,
        workspace_id=workspace_id,
        installation_id=installation_id,
        github_pull_request_id=1,
        number=7,
        title="PR",
        state=GitHubPullRequestState.open,
        head_sha="abc123",
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )

    repository = GitHubRepositoryORM(
        installation_id=installation_id,
        workspace_id=workspace_id,
        github_repository_id=10,
        name="demo",
        full_name="acme/demo",
        private=False,
        status=GitHubRepositoryStatus.active,
    )

    installation = GitHubInstallationORM(
        workspace_id=workspace_id,
        github_installation_id=12345,
        account_login="acme",
        account_type=GitHubAccountType.organization,
        account_id=1,
    )

    session = AsyncMock()
    session.get = AsyncMock(
        side_effect=[revision, pull_request, repository, installation]
    )

    create_mock = AsyncMock(return_value=77)
    with patch("app.services.github_pipeline_trace.settings") as mock_settings:
        mock_settings.github_api_enabled = True
        with patch(
            "app.services.github_pipeline_trace.github_api.create_check_run",
            create_mock,
        ):
            check_run_id = await start_pipeline_github_check(
                session,
                pipeline_run=pipeline_run,
            )

    assert check_run_id == 77
    create_mock.assert_awaited_once()
    assert create_mock.await_args.kwargs["status"] == "in_progress"
    assert "Revy review in progress" in create_mock.await_args.kwargs["summary"]
