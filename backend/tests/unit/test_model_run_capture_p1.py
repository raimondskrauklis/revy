# backend/tests/unit/test_model_run_capture_p1.py
"""Model run capture P1 — manifest/attempt parity and publish step models."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.constants.enums import (
    GitHubPublishJobStatus,
    PipelineStepType,
)
from app.models.github_publish_job import GitHubPublishJobORM
from app.services.github_pipeline_trace import (
    record_judge_pipeline_step,
    record_publish_pipeline_step,
)


@pytest.mark.asyncio
async def test_embed_model_parity_manifest_matches_attempt_request_model():
    from app.integrations.voyage_embeddings import VoyageEmbedRecorderContext, embed_texts

    pipeline_run_id = uuid.uuid4()
    index_job_id = uuid.uuid4()
    model = "voyage-code-3.5"
    recorder = VoyageEmbedRecorderContext(
        pipeline_run_id=pipeline_run_id,
        index_job_id=index_job_id,
        request_model=model,
    )
    response = MagicMock()
    response.status_code = 200
    response.json.return_value = {"data": [{"embedding": [0.1]}]}
    response.raise_for_status = MagicMock()
    client = AsyncMock()
    client.post = AsyncMock(return_value=response)

    captured_request_model = None

    async def _capture_start(context):
        nonlocal captured_request_model
        captured_request_model = context.request_model
        return uuid.uuid4()

    with patch("app.integrations.voyage_embeddings.settings") as mock_settings:
        mock_settings.embeddings_enabled = True
        mock_settings.voyage_api_key = "key"
        mock_settings.revy_embedding_model = model
        mock_settings.revy_embedding_dimensions = 1024
        with patch(
            "app.integrations.voyage_embeddings.try_start_attempt",
            side_effect=_capture_start,
        ):
            with patch("app.integrations.voyage_embeddings.try_complete_attempt", AsyncMock()):
                await embed_texts(client, ["x"], request_model=model, recorder=recorder)

    assert captured_request_model == model


@pytest.mark.asyncio
async def test_judge_pipeline_step_stores_model_fields():
    pipeline_run_id = uuid.uuid4()
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()

    await record_judge_pipeline_step(
        session,
        pipeline_run_id=pipeline_run_id,
        judged_count=1,
        duration_ms=100,
        model_provider="anthropic",
        model_id="claude-sonnet-4",
    )

    step = session.add.call_args_list[0].args[0]
    assert step.step_type == PipelineStepType.judge
    assert step.model_provider == "anthropic"
    assert step.model_id == "claude-sonnet-4"


@pytest.mark.asyncio
async def test_publish_model_fields_only_when_moonshot_output_used():
    from app.services.github_publish_formatter import (
        PublishFormatContext,
        build_pr_review_comment_with_model,
    )

    ctx = PublishFormatContext(
        pull_request_id=uuid.uuid4(),
        pull_request_number=42,
        head_sha="abc",
        revision_number=1,
        groups=[],
        pipeline_run_id=uuid.uuid4(),
        review_run_id=uuid.uuid4(),
    )

    with patch("app.services.github_publish_formatter.settings") as mock_settings:
        mock_settings.reviewer_llm_enabled.return_value = True
        mock_settings.revy_revision_timeout_standard_seconds = 60
        mock_settings.revy_moonshot_model_for_profile.return_value = "kimi-k2.7-code"
        with patch(
            "app.services.github_publish_formatter.moonshot_review.complete_issue_comment_markdown",
            AsyncMock(side_effect=OSError("offline")),
        ):
            _, provider, model_id = await build_pr_review_comment_with_model(ctx)

    assert provider is None
    assert model_id is None


@pytest.mark.asyncio
async def test_publish_model_on_pipeline_step():
    pipeline_run_id = uuid.uuid4()
    job = GitHubPublishJobORM(
        review_run_id=uuid.uuid4(),
        revision_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        head_sha="abc",
        status=GitHubPublishJobStatus.completed,
    )
    job.id = uuid.uuid4()
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()

    await record_publish_pipeline_step(
        session,
        pipeline_run_id=pipeline_run_id,
        job=job,
        summary_markdown="summary",
        duration_ms=50,
        model_provider="moonshot",
        model_id="kimi-k2.7-code",
    )

    step = session.add.call_args_list[0].args[0]
    assert step.model_provider == "moonshot"
    assert step.model_id == "kimi-k2.7-code"


@pytest.mark.asyncio
async def test_review_model_request_matches_run_model_id():
    import inspect

    from app.constants.enums import LlmCallOperationName, LlmCallStepType
    from app.services.github_review import _call_llm
    from app.services.llm_call_recorder import LlmAttemptStartContext
    from app.services.model_policy import ModelRef

    assert "recorder" in inspect.signature(_call_llm).parameters

    model_ref = ModelRef(provider="moonshot", model_id="kimi-k2.7-code")

    with patch(
        "app.services.github_review.llm_dispatch.call_review_llm",
        AsyncMock(return_value='{"findings":[]}'),
    ):
        with patch(
            "app.services.github_review.start_attempt",
            AsyncMock(return_value=uuid.uuid4()),
        ) as start_mock:
            with patch("app.services.github_review.settings") as mock_settings:
                mock_settings.revy_revision_llm_http_timeout_seconds.return_value = 30.0
                recorder = LlmAttemptStartContext(
                    pipeline_run_id=uuid.uuid4(),
                    review_run_id=uuid.uuid4(),
                    index_job_id=None,
                    step_type=LlmCallStepType.review,
                    operation_name=LlmCallOperationName.chat,
                    attempt_no=0,
                    provider=model_ref.provider,
                    request_model=model_ref.model_id,
                )
                await _call_llm(
                    model_ref=model_ref,
                    profile="standard",
                    prompt="test",
                    recorder=recorder,
                )

    start_mock.assert_awaited_once_with(recorder)
