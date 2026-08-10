# backend/app/services/llm_call_recorder.py
"""Durable LLM attempt rows — pipeline observability."""
from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import (
    GitHubReviewRunFailureClass,
    LlmCallOperationName,
    LlmCallStepType,
)
from app.core.database import get_db_context
from app.models.base import utc_now
from app.models.github_llm_call_attempt import GitHubLlmCallAttemptORM
from app.services.observability_failure import classify_failure_class


@dataclass(frozen=True, slots=True)
class LlmAttemptStartContext:
    pipeline_run_id: UUID
    review_run_id: UUID | None
    index_job_id: UUID | None
    step_type: LlmCallStepType
    operation_name: LlmCallOperationName
    attempt_no: int
    provider: str
    request_model: str
    batch_size: int | None = None


@dataclass(frozen=True, slots=True)
class LlmAttemptCompleteContext:
    response_model: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    finish_reason: str | None = None
    wait_ms: int | None = None
    http_status: int | None = None
    response_text: str | None = None


@dataclass(frozen=True, slots=True)
class LlmAttemptFailContext:
    failure_class: GitHubReviewRunFailureClass | None = None
    wait_ms: int | None = None
    http_status: int | None = None
    response_text: str | None = None


def _preview_and_hash(response_text: str | None) -> tuple[str | None, str | None]:
    if not response_text:
        return None, None
    preview = response_text[:512]
    digest = hashlib.sha256(response_text.encode("utf-8")).hexdigest()
    return preview, digest


async def start_attempt(context: LlmAttemptStartContext) -> UUID:
    async with get_db_context() as session:
        row = GitHubLlmCallAttemptORM(
            pipeline_run_id=context.pipeline_run_id,
            review_run_id=context.review_run_id,
            index_job_id=context.index_job_id,
            step_type=context.step_type,
            operation_name=context.operation_name,
            attempt_no=context.attempt_no,
            provider=context.provider,
            request_model=context.request_model,
            batch_size=context.batch_size,
            started_at=utc_now(),
        )
        session.add(row)
        await session.flush()
        return row.id


async def complete_attempt(
    attempt_id: UUID,
    *,
    context: LlmAttemptCompleteContext,
) -> None:
    preview, digest = _preview_and_hash(context.response_text)
    async with get_db_context() as session:
        row = await session.get(GitHubLlmCallAttemptORM, attempt_id)
        if row is None:
            return
        row.response_model = context.response_model
        row.input_tokens = context.input_tokens
        row.output_tokens = context.output_tokens
        row.finish_reason = context.finish_reason
        row.wait_ms = context.wait_ms
        row.http_status = context.http_status
        row.response_preview = preview
        row.response_sha256 = digest
        row.completed_at = datetime.now(UTC)


async def fail_attempt(
    attempt_id: UUID,
    *,
    context: LlmAttemptFailContext,
    exc: BaseException | None = None,
) -> None:
    failure_class = context.failure_class
    if failure_class is None and exc is not None:
        failure_class = classify_failure_class(exc)
    preview, digest = _preview_and_hash(context.response_text)
    async with get_db_context() as session:
        row = await session.get(GitHubLlmCallAttemptORM, attempt_id)
        if row is None:
            return
        row.failure_class = failure_class
        row.wait_ms = context.wait_ms
        row.http_status = context.http_status
        row.response_preview = preview
        row.response_sha256 = digest
        row.completed_at = datetime.now(UTC)


async def next_review_llm_attempt_no(
    *,
    review_run_id: UUID,
    session: AsyncSession | None = None,
) -> int:
    async def _next(sess: AsyncSession) -> int:
        max_attempt = await sess.scalar(
            select(func.max(GitHubLlmCallAttemptORM.attempt_no)).where(
                GitHubLlmCallAttemptORM.review_run_id == review_run_id,
                GitHubLlmCallAttemptORM.step_type == LlmCallStepType.review,
            )
        )
        return int(max_attempt if max_attempt is not None else -1) + 1

    if session is not None:
        return await _next(session)
    async with get_db_context() as dedicated_session:
        return await _next(dedicated_session)


async def list_attempts_for_review_run(review_run_id: UUID) -> list[GitHubLlmCallAttemptORM]:
    async with get_db_context() as session:
        rows = await session.scalars(
            select(GitHubLlmCallAttemptORM).where(
                GitHubLlmCallAttemptORM.review_run_id == review_run_id,
            )
        )
        return list(rows.all())
