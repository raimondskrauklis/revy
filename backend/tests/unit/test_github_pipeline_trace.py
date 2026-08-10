# backend/tests/unit/test_github_pipeline_trace.py
"""GitHub pipeline trace service — review-quality RQ3."""
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.constants.enums import (
    GitHubAccountType,
    GitHubIndexJobStatus,
    GitHubIndexJobTriggerSource,
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
    get_resolution_metrics_for_review_run,
    provision_queued_pipeline_github_check,
    purge_old_pipeline_artifacts,
    record_index_pipeline_step,
    record_reconcile_pipeline_step,
    record_review_pipeline_step,
    stash_pipeline_github_check_run_id,
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
    job.index_manifest_stats = {
        "reused_count": 0,
        "new_count": 2,
        "embed_batches": 1,
        "embedding_provider": "voyage",
        "embedding_model": "voyage-code-3.5",
        "embedding_dimensions": 1024,
    }

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
    step = session.add.call_args_list[0].args[0]
    assert step.model_provider == "voyage"
    assert step.model_id == "voyage-code-3.5"
    manifest_artifact = session.add.call_args_list[1].args[0]
    assert manifest_artifact.content_json["embedding_model"] == "voyage-code-3.5"
    assert manifest_artifact.content_json["embedding_dimensions"] == 1024


@pytest.mark.asyncio
async def test_record_index_pipeline_step_reused_chunks_omits_embedding_model():
    pipeline_run_id = uuid.uuid4()
    job = GitHubIndexJobORM(
        revision_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        status=GitHubIndexJobStatus.completed,
        index_mode=GitHubIndexMode.diff,
        chunk_count=5,
    )
    job.id = uuid.uuid4()
    job.index_manifest_stats = {
        "reused_count": 5,
        "new_count": 0,
        "embed_batches": 0,
    }

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.flush = AsyncMock()

    await record_index_pipeline_step(
        session,
        pipeline_run_id=pipeline_run_id,
        job=job,
        duration_ms=500,
    )

    step = session.add.call_args_list[0].args[0]
    assert step.model_provider is None
    assert step.model_id is None
    manifest_artifact = session.add.call_args_list[1].args[0]
    assert manifest_artifact.content_json["embedding_skipped_reason"] == "reused_chunks_only"
    assert "embedding_model" not in manifest_artifact.content_json


@pytest.mark.asyncio
async def test_record_index_pipeline_step_updates_pending_step_model_fields():
    pipeline_run_id = uuid.uuid4()
    pending_step = GitHubPipelineStepORM(
        pipeline_run_id=pipeline_run_id,
        step_type=PipelineStepType.index,
        status=PipelineStepStatus.pending,
        duration_ms=0,
    )
    pending_step.id = uuid.uuid4()
    manifest_artifact = GitHubPipelineArtifactORM(
        step_id=pending_step.id,
        kind=PipelineArtifactKind.manifest,
        content_json={"github_check_run_id": 42},
    )

    job = GitHubIndexJobORM(
        revision_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        status=GitHubIndexJobStatus.completed,
        index_mode=GitHubIndexMode.diff,
        chunk_count=3,
    )
    job.id = uuid.uuid4()
    job.index_manifest_stats = {
        "reused_count": 0,
        "new_count": 3,
        "embed_batches": 1,
        "embedding_provider": "voyage",
        "embedding_model": "voyage-code-3.5",
        "embedding_dimensions": 1024,
    }

    session = AsyncMock()
    session.scalar = AsyncMock(
        side_effect=[pending_step, manifest_artifact, pending_step, manifest_artifact],
    )
    session.add = MagicMock()
    session.flush = AsyncMock()

    await stash_pipeline_github_check_run_id(
        session,
        pipeline_run_id=pipeline_run_id,
        github_check_run_id=42,
    )
    await record_index_pipeline_step(
        session,
        pipeline_run_id=pipeline_run_id,
        job=job,
        duration_ms=1200,
    )

    assert pending_step.model_provider == "voyage"
    assert pending_step.model_id == "voyage-code-3.5"
    assert manifest_artifact.content_json["embedding_model"] == "voyage-code-3.5"


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


@pytest.mark.asyncio
async def test_provision_queued_pipeline_github_check_creates_check_for_pending_job():
    workspace_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pipeline_run_id = uuid.uuid4()

    job = GitHubIndexJobORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubIndexJobStatus.pending,
        trigger_source=GitHubIndexJobTriggerSource.autostart,
        index_mode=GitHubIndexMode.diff,
    )
    job.id = uuid.uuid4()

    pipeline_run = GitHubPipelineRunORM(
        workspace_id=workspace_id,
        revision_id=revision_id,
        head_sha="abc123",
        index_mode=GitHubIndexMode.diff,
    )
    pipeline_run.id = pipeline_run_id

    session = AsyncMock()
    create_mock = AsyncMock(return_value=88)

    with patch("app.services.github_pipeline_trace.settings") as mock_settings:
        mock_settings.github_api_enabled = True
        with patch(
            "app.services.github_pipeline_trace.ensure_pipeline_run_for_index_job",
            AsyncMock(return_value=pipeline_run),
        ):
            with patch(
                "app.services.github_pipeline_trace.resolve_pipeline_github_check_run_id",
                AsyncMock(return_value=None),
            ):
                with patch(
                    "app.services.github_pipeline_trace._pipeline_check_repo_context",
                    AsyncMock(return_value=(12345, "acme", "demo", "abc123", 7)),
                ):
                    with patch(
                        "app.services.github_pipeline_trace.github_api.create_check_run",
                        create_mock,
                    ):
                        with patch(
                            "app.services.github_pipeline_trace.stash_pipeline_github_check_run_id",
                            AsyncMock(),
                        ) as stash_mock:
                            check_run_id = await provision_queued_pipeline_github_check(
                                session,
                                job=job,
                                head_sha="abc123",
                            )

    assert check_run_id == 88
    create_mock.assert_awaited_once()
    assert "queued" in create_mock.await_args.kwargs["summary"].lower()
    stash_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_start_pipeline_github_check_reuses_provisioned_check():
    pipeline_run = GitHubPipelineRunORM(
        workspace_id=uuid.uuid4(),
        revision_id=uuid.uuid4(),
        head_sha="abc123",
        index_mode=GitHubIndexMode.diff,
    )
    pipeline_run.id = uuid.uuid4()
    session = AsyncMock()

    with patch("app.services.github_pipeline_trace.settings") as mock_settings:
        mock_settings.github_api_enabled = True
        with patch(
            "app.services.github_pipeline_trace.resolve_pipeline_github_check_run_id",
            AsyncMock(return_value=55),
        ):
            with patch(
                "app.services.github_pipeline_trace._revision_is_pull_request_head",
                AsyncMock(return_value=True),
            ):
                with patch(
                    "app.services.github_pipeline_trace.refresh_pipeline_github_check_in_progress",
                    AsyncMock(),
                ) as refresh_mock:
                    with patch(
                        "app.services.github_pipeline_trace.github_api.create_check_run",
                        AsyncMock(),
                    ) as create_mock:
                        check_run_id = await start_pipeline_github_check(
                            session,
                            pipeline_run=pipeline_run,
                        )

    assert check_run_id == 55
    create_mock.assert_not_awaited()
    refresh_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_start_pipeline_github_check_skips_refresh_when_not_head():
    pipeline_run = GitHubPipelineRunORM(
        workspace_id=uuid.uuid4(),
        revision_id=uuid.uuid4(),
        head_sha="abc123",
        index_mode=GitHubIndexMode.diff,
    )
    pipeline_run.id = uuid.uuid4()
    session = AsyncMock()

    with patch("app.services.github_pipeline_trace.settings") as mock_settings:
        mock_settings.github_api_enabled = True
        with patch(
            "app.services.github_pipeline_trace.resolve_pipeline_github_check_run_id",
            AsyncMock(return_value=55),
        ):
            with patch(
                "app.services.github_pipeline_trace._revision_is_pull_request_head",
                AsyncMock(return_value=False),
            ):
                with patch(
                    "app.services.github_pipeline_trace.refresh_pipeline_github_check_in_progress",
                    AsyncMock(),
                ) as refresh_mock:
                    check_run_id = await start_pipeline_github_check(
                        session,
                        pipeline_run=pipeline_run,
                    )

    assert check_run_id is None
    refresh_mock.assert_not_awaited()


@pytest.mark.asyncio
async def test_record_generation_superseded_on_pipeline_writes_index_manifest():
    pipeline_run_id = uuid.uuid4()
    review_run_id = uuid.uuid4()
    step_id = uuid.uuid4()

    pipeline_run = GitHubPipelineRunORM(
        workspace_id=uuid.uuid4(),
        revision_id=uuid.uuid4(),
        head_sha="abc",
        review_run_id=review_run_id,
    )
    pipeline_run.id = pipeline_run_id

    step = GitHubPipelineStepORM(
        pipeline_run_id=pipeline_run_id,
        step_type=PipelineStepType.index,
        status=PipelineStepStatus.completed,
        duration_ms=100,
    )
    step.id = step_id

    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[pipeline_run, step, None])
    session.add = MagicMock()
    session.flush = AsyncMock()

    from app.services.github_pipeline_trace import record_generation_superseded_on_pipeline

    await record_generation_superseded_on_pipeline(session, review_run_id=review_run_id)

    assert session.add.call_count == 1
    artifact = session.add.call_args.args[0]
    assert artifact.kind == PipelineArtifactKind.manifest
    assert "generation_superseded_at" in artifact.content_json


@pytest.mark.asyncio
async def test_record_publish_skip_on_pipeline_writes_manifest_flag():
    pipeline_run_id = uuid.uuid4()
    review_run_id = uuid.uuid4()

    pipeline_run = GitHubPipelineRunORM(
        workspace_id=uuid.uuid4(),
        revision_id=uuid.uuid4(),
        head_sha="abc",
        review_run_id=review_run_id,
    )
    pipeline_run.id = pipeline_run_id

    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[pipeline_run, None, None])
    session.add = MagicMock()
    session.flush = AsyncMock()

    from app.services.github_pipeline_trace import record_publish_skip_on_pipeline

    await record_publish_skip_on_pipeline(
        session,
        review_run_id=review_run_id,
        manifest_key="publish_skipped_not_head",
    )

    assert session.add.call_count >= 2
    manifest_artifact = next(
        call.args[0]
        for call in session.add.call_args_list
        if getattr(call.args[0], "kind", None) == PipelineArtifactKind.manifest
    )
    assert manifest_artifact.content_json["publish_skipped_not_head"] is True


@pytest.mark.asyncio
async def test_record_judge_pipeline_step_includes_verification_manifest():
    from app.services.github_finding_judge import JudgeCandidateArtifact
    from app.services.github_pipeline_trace import record_judge_pipeline_step

    pipeline_run_id = uuid.uuid4()
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.flush = AsyncMock()

    verification_artifact = JudgeCandidateArtifact(
        group_id=uuid.uuid4(),
        evidence_snippet="snippet",
        user_prompt="verify",
        raw_response={"outcome": "dismissed", "usage": {"input_tokens": 50, "output_tokens": 5}},
        outcome="dismissed",
        file_patch_chars=42,
        input_tokens=50,
        output_tokens=5,
    )

    await record_judge_pipeline_step(
        session,
        pipeline_run_id=pipeline_run_id,
        judged_count=1,
        duration_ms=100,
        candidates=[],
        verification_judged_count=1,
        verification_candidates=[verification_artifact],
    )

    step = next(
        call.args[0]
        for call in session.add.call_args_list
        if getattr(call.args[0], "step_type", None) == PipelineStepType.judge
    )
    assert step.input_tokens == 50
    assert step.output_tokens == 5

    manifest_artifact = next(
        call.args[0]
        for call in session.add.call_args_list
        if getattr(call.args[0], "kind", None) == PipelineArtifactKind.manifest
    )
    assert manifest_artifact.content_json["verification_judged_count"] == 1
    assert len(manifest_artifact.content_json["verification_candidates"]) == 1
    assert manifest_artifact.content_json["verification_group_ids"]


@pytest.mark.asyncio
async def test_record_judge_pipeline_step_serializes_failure_fields():
    from app.services.github_finding_judge import JudgeCandidateArtifact
    from app.services.github_pipeline_trace import record_judge_pipeline_step

    pipeline_run_id = uuid.uuid4()
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.flush = AsyncMock()

    failed_artifact = JudgeCandidateArtifact(
        group_id=uuid.uuid4(),
        evidence_snippet="snippet",
        user_prompt="judge",
        raw_response=None,
        raw_response_text='{"broken": ',
        parse_error="judge_json_invalid",
        outcome=None,
        file_patch_chars=100,
    )

    await record_judge_pipeline_step(
        session,
        pipeline_run_id=pipeline_run_id,
        judged_count=0,
        duration_ms=50,
        candidates=[failed_artifact],
    )

    manifest_artifact = next(
        call.args[0]
        for call in session.add.call_args_list
        if getattr(call.args[0], "kind", None) == PipelineArtifactKind.manifest
    )
    candidate = manifest_artifact.content_json["candidates"][0]
    assert candidate["parse_error"] == "judge_json_invalid"
    assert candidate["raw_response_text"] == '{"broken": '
    assert candidate["raw_response"] is None


@pytest.mark.asyncio
async def test_record_judge_pipeline_step_serializes_retry_count():
    from app.services.github_finding_judge import JudgeCandidateArtifact
    from app.services.github_pipeline_trace import record_judge_pipeline_step

    pipeline_run_id = uuid.uuid4()
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.flush = AsyncMock()

    artifact = JudgeCandidateArtifact(
        group_id=uuid.uuid4(),
        evidence_snippet="snippet",
        user_prompt="judge",
        raw_response={"outcome": "dismissed"},
        outcome="dismissed",
        retry_count=1,
    )

    await record_judge_pipeline_step(
        session,
        pipeline_run_id=pipeline_run_id,
        judged_count=1,
        duration_ms=50,
        candidates=[artifact],
    )

    manifest_artifact = next(
        call.args[0]
        for call in session.add.call_args_list
        if getattr(call.args[0], "kind", None) == PipelineArtifactKind.manifest
    )
    assert manifest_artifact.content_json["candidates"][0]["retry_count"] == 1


@pytest.mark.asyncio
async def test_record_reconcile_pipeline_step_writes_resolution_pass():
    pipeline_run_id = uuid.uuid4()
    resolution_pass = {
        "transition_count": 2,
        "denominator_active_prior": 4,
        "resolution_rate_pct": 50.0,
    }

    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()

    await record_reconcile_pipeline_step(
        session,
        pipeline_run_id=pipeline_run_id,
        group_count=3,
        duration_ms=50,
        resolution_pass=resolution_pass,
    )

    manifest_artifact = next(
        call.args[0]
        for call in session.add.call_args_list
        if getattr(call.args[0], "kind", None) == PipelineArtifactKind.manifest
    )
    assert manifest_artifact.content_json["linked_group_count"] == 3
    assert manifest_artifact.content_json["resolution_pass"] == resolution_pass


@pytest.mark.asyncio
async def test_get_resolution_metrics_for_review_run_reads_reconcile_manifest():
    review_run_id = uuid.uuid4()
    pipeline_run_id = uuid.uuid4()
    step_id = uuid.uuid4()
    resolution_pass = {"resolution_rate_pct": 75.0, "transition_count": 3}

    pipeline_run = GitHubPipelineRunORM(
        workspace_id=uuid.uuid4(),
        review_run_id=review_run_id,
        head_sha="abc",
    )
    pipeline_run.id = pipeline_run_id

    reconcile_step = GitHubPipelineStepORM(
        pipeline_run_id=pipeline_run_id,
        step_type=PipelineStepType.reconcile,
        status=PipelineStepStatus.completed,
        duration_ms=10,
    )
    reconcile_step.id = step_id

    manifest_artifact = GitHubPipelineArtifactORM(
        step_id=step_id,
        kind=PipelineArtifactKind.manifest,
        content_json={"linked_group_count": 1, "resolution_pass": resolution_pass},
    )

    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[pipeline_run, reconcile_step, manifest_artifact])

    result = await get_resolution_metrics_for_review_run(
        session,
        review_run_id=review_run_id,
    )

    assert result == resolution_pass


@pytest.mark.asyncio
async def test_record_publish_pipeline_step_rollup_pass():
    from app.constants.enums import GitHubPublishJobStatus
    from app.models.github_publish_job import GitHubPublishJobORM
    from app.services.github_pipeline_trace import record_publish_pipeline_step

    pipeline_run_id = uuid.uuid4()
    job = GitHubPublishJobORM(
        review_run_id=uuid.uuid4(),
        revision_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        head_sha="abc",
        status=GitHubPublishJobStatus.completed,
    )
    job.id = uuid.uuid4()
    job.summary_json = {
        "pr_resolution_rollup": {
            "raised_count": 5,
            "resolved_count": 2,
            "still_open_display": 3,
            "review_count": 2,
        }
    }

    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()

    await record_publish_pipeline_step(
        session,
        pipeline_run_id=pipeline_run_id,
        job=job,
        summary_markdown="check",
        issue_comment_markdown="issue",
        duration_ms=10,
    )

    manifest_artifact = next(
        call.args[0]
        for call in session.add.call_args_list
        if getattr(call.args[0], "kind", None) == PipelineArtifactKind.manifest
    )
    assert manifest_artifact.content_json["rollup_pass"]["review_count"] == 2
