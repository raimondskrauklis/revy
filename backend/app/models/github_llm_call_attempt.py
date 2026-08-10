# backend/app/models/github_llm_call_attempt.py
"""Per-HTTP LLM call attempts — pipeline observability."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.enums import (
    GitHubReviewRunFailureClass,
    LlmCallOperationName,
    LlmCallStepType,
)
from app.models.base import TimestampedModel


class GitHubLlmCallAttemptORM(TimestampedModel):
    __tablename__ = "github_llm_call_attempts"
    __table_args__ = (
        Index("ix_github_llm_call_attempts_pipeline_run_id", "pipeline_run_id"),
        Index(
            "ix_github_llm_call_attempts_review_run_step",
            "review_run_id",
            "step_type",
        ),
        Index("ix_github_llm_call_attempts_started_at", "started_at"),
        Index(
            "ix_github_llm_call_attempts_provider_model",
            "provider",
            "request_model",
        ),
    )

    pipeline_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("github_pipeline_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    review_run_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("github_review_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    index_job_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("github_index_jobs.id", ondelete="SET NULL"),
        nullable=True,
    )
    step_type: Mapped[LlmCallStepType] = mapped_column(String(length=32), nullable=False)
    operation_name: Mapped[LlmCallOperationName] = mapped_column(
        String(length=32),
        nullable=False,
    )
    attempt_no: Mapped[int] = mapped_column(Integer, nullable=False, default=0, server_default="0")
    provider: Mapped[str] = mapped_column(String(length=32), nullable=False)
    request_model: Mapped[str] = mapped_column(String(length=128), nullable=False)
    response_model: Mapped[str | None] = mapped_column(String(length=128), nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    finish_reason: Mapped[str | None] = mapped_column(String(length=64), nullable=True)
    wait_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    http_status: Mapped[int | None] = mapped_column(Integer, nullable=True)
    failure_class: Mapped[GitHubReviewRunFailureClass | None] = mapped_column(
        String(length=32),
        nullable=True,
    )
    response_preview: Mapped[str | None] = mapped_column(String(length=512), nullable=True)
    response_sha256: Mapped[str | None] = mapped_column(String(length=64), nullable=True)
    batch_size: Mapped[int | None] = mapped_column(Integer, nullable=True)
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
