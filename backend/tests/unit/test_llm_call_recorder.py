# backend/tests/unit/test_llm_call_recorder.py
"""Pipeline observability P0 — LlmCallRecorder."""
import uuid
from contextlib import asynccontextmanager
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.constants.enums import (
    GitHubReviewRunFailureClass,
    LlmCallOperationName,
    LlmCallStepType,
)
from app.services.llm_call_recorder import (
    LlmAttemptCompleteContext,
    LlmAttemptFailContext,
    LlmAttemptStartContext,
    complete_attempt,
    fail_attempt,
    start_attempt,
)


@pytest.mark.asyncio
async def test_start_attempt_uses_dedicated_session():
    row_id = uuid.uuid4()
    session = AsyncMock()
    row = MagicMock()
    row.id = row_id

    @asynccontextmanager
    async def fake_db_context():
        yield session

    with patch("app.services.llm_call_recorder.get_db_context", fake_db_context):
        with patch("app.services.llm_call_recorder.GitHubLlmCallAttemptORM", return_value=row):
            attempt_id = await start_attempt(
                LlmAttemptStartContext(
                    pipeline_run_id=uuid.uuid4(),
                    review_run_id=uuid.uuid4(),
                    index_job_id=None,
                    step_type=LlmCallStepType.review,
                    operation_name=LlmCallOperationName.chat,
                    attempt_no=0,
                    provider="moonshot",
                    request_model="kimi-k2.7-code",
                )
            )
    assert attempt_id == row_id
    session.add.assert_called_once()
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_fail_attempt_sets_failure_class():
    attempt_id = uuid.uuid4()
    session = AsyncMock()
    row = MagicMock()
    row.completed_at = None
    session.get = AsyncMock(return_value=row)

    @asynccontextmanager
    async def fake_db_context():
        yield session

    with patch("app.services.llm_call_recorder.get_db_context", fake_db_context):
        await fail_attempt(
            attempt_id,
            context=LlmAttemptFailContext(
                failure_class=GitHubReviewRunFailureClass.timeout,
                wait_ms=1200,
            ),
        )
    assert row.failure_class == GitHubReviewRunFailureClass.timeout
    assert row.wait_ms == 1200
    assert row.completed_at is not None


@pytest.mark.asyncio
async def test_complete_attempt_sets_tokens():
    attempt_id = uuid.uuid4()
    session = AsyncMock()
    row = MagicMock()
    session.get = AsyncMock(return_value=row)

    @asynccontextmanager
    async def fake_db_context():
        yield session

    with patch("app.services.llm_call_recorder.get_db_context", fake_db_context):
        await complete_attempt(
            attempt_id,
            context=LlmAttemptCompleteContext(
                input_tokens=10,
                output_tokens=20,
                wait_ms=500,
            ),
        )
    assert row.input_tokens == 10
    assert row.output_tokens == 20
