# backend/tests/unit/test_review_observability_po_v3.py
"""Pipeline observability PO-V3 — HTTP timeout durability."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.constants.enums import (
    GitHubIndexJobStatus,
    GitHubIndexMode,
    GitHubPullRequestState,
    GitHubReviewRunFailureClass,
    GitHubReviewRunStatus,
    LlmCallOperationName,
    LlmCallStepType,
    ReviewProfile,
)
from app.core.worker_retries import WorkerRetryableError
from app.models.github_index_job import GitHubIndexJobORM
from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
from app.models.github_review_run import GitHubReviewRunORM
from app.services import github_review
from app.services.llm_call_recorder import LlmAttemptStartContext
from app.services.model_policy import ModelRef


def _session_execute_mock() -> AsyncMock:
    result = MagicMock()
    result.rowcount = 1
    return AsyncMock(return_value=result)


@pytest.mark.asyncio
async def test_http_timeout_writes_attempt_row_and_checkpoint_survives():
    review_run_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    pipeline_run_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.pending,
        profile=ReviewProfile.standard,
    )
    run.id = review_run_id

    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request_id,
        revision_number=1,
        head_sha="abc",
    )
    revision.id = revision_id

    pull_request = GitHubPullRequestORM(
        repository_id=repository_id,
        workspace_id=workspace_id,
        installation_id=uuid.uuid4(),
        github_pull_request_id=1,
        number=1,
        title="Fix",
        state=GitHubPullRequestState.open,
        head_sha="abc",
        head_ref="feature",
        base_ref="main",
        revision_count=1,
    )
    pull_request.id = pull_request_id

    index_job = GitHubIndexJobORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubIndexJobStatus.completed,
        index_mode=GitHubIndexMode.diff,
    )

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[run, revision, pull_request])
    session.flush = AsyncMock()
    session.execute = _session_execute_mock()
    session.refresh = AsyncMock()
    session.scalar = AsyncMock(return_value=None)

    pipeline_run = MagicMock()
    pipeline_run.id = pipeline_run_id

    context_pack = github_review.ReviewContextPack(
        prompt="review prompt",
        manifest={"index_mode": "diff"},
    )

    timeout_exc = httpx.ReadTimeout("timed out")

    with patch(
        "app.services.github_review.get_latest_completed_index_job",
        AsyncMock(return_value=index_job),
    ):
        with patch(
            "app.services.github_review.prepare_review_context",
            AsyncMock(return_value=context_pack),
        ):
            with patch(
                "app.services.github_review.resolve_model",
                AsyncMock(return_value=ModelRef(provider="moonshot", model_id="kimi-k2.7-code")),
            ):
                with patch(
                    "app.services.github_review.commit_review_run_observability_checkpoint",
                    AsyncMock(),
                ) as checkpoint_mock:
                    with patch(
                        "app.services.github_review.get_pipeline_run_for_review_run",
                        AsyncMock(return_value=pipeline_run),
                    ):
                        with patch(
                            "app.services.github_review._call_llm",
                            AsyncMock(side_effect=timeout_exc),
                        ):
                            with patch(
                                "app.services.github_review.classify_transient_error",
                                return_value=WorkerRetryableError(str(timeout_exc)),
                            ):
                                with pytest.raises(WorkerRetryableError):
                                    await github_review.run_review_run(
                                        session,
                                        review_run_id=review_run_id,
                                    )
    checkpoint_mock.assert_awaited_once()


@pytest.mark.asyncio
async def test_call_llm_timeout_records_failed_attempt():
    model_ref = ModelRef(provider="moonshot", model_id="kimi-k2.7-code")
    recorder = LlmAttemptStartContext(
        pipeline_run_id=uuid.uuid4(),
        review_run_id=uuid.uuid4(),
        index_job_id=None,
        step_type=LlmCallStepType.review,
        operation_name=LlmCallOperationName.chat,
        attempt_no=0,
        provider="moonshot",
        request_model="kimi-k2.7-code",
    )

    with patch(
        "app.services.github_review.start_attempt",
        AsyncMock(return_value=uuid.uuid4()),
    ) as start_mock:
        with patch("app.services.github_review.fail_attempt", AsyncMock()) as fail_mock:
            with patch(
                "app.services.github_review.llm_dispatch.call_review_llm",
                AsyncMock(side_effect=httpx.ReadTimeout("timed out")),
            ):
                with patch("app.services.github_review.settings") as settings_mock:
                    settings_mock.revy_revision_llm_http_timeout_seconds.return_value = 60
                    with pytest.raises(httpx.ReadTimeout):
                        await github_review._call_llm(
                            model_ref=model_ref,
                            profile="standard",
                            prompt="hello",
                            recorder=recorder,
                        )
    start_mock.assert_awaited_once()
    fail_mock.assert_awaited_once()
    fail_context = fail_mock.await_args.kwargs["context"]
    assert fail_context.failure_class == GitHubReviewRunFailureClass.timeout


@pytest.mark.asyncio
async def test_call_llm_http_status_error_records_status():
    model_ref = ModelRef(provider="moonshot", model_id="kimi-k2.7-code")
    recorder = LlmAttemptStartContext(
        pipeline_run_id=uuid.uuid4(),
        review_run_id=uuid.uuid4(),
        index_job_id=None,
        step_type=LlmCallStepType.review,
        operation_name=LlmCallOperationName.chat,
        attempt_no=0,
        provider="moonshot",
        request_model="kimi-k2.7-code",
    )
    request = httpx.Request("POST", "https://api.example.com/v1/chat")
    response = httpx.Response(429, request=request)
    status_exc = httpx.HTTPStatusError("rate limited", request=request, response=response)

    with patch(
        "app.services.github_review.start_attempt",
        AsyncMock(return_value=uuid.uuid4()),
    ):
        with patch("app.services.github_review.fail_attempt", AsyncMock()) as fail_mock:
            with patch(
                "app.services.github_review.llm_dispatch.call_review_llm",
                AsyncMock(side_effect=status_exc),
            ):
                with patch("app.services.github_review.settings") as settings_mock:
                    settings_mock.revy_revision_llm_http_timeout_seconds.return_value = 60
                    with pytest.raises(httpx.HTTPStatusError):
                        await github_review._call_llm(
                            model_ref=model_ref,
                            profile="standard",
                            prompt="hello",
                            recorder=recorder,
                        )
    fail_context = fail_mock.await_args.kwargs["context"]
    assert fail_context.http_status == 429
