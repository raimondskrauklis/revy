# backend/app/models/github_pipeline.py
"""GitHub pipeline trace — review-quality explainability (O)."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import CheckConstraint, ForeignKey, Index, Integer, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.constants.enums import (
    GitHubIndexMode,
    PipelineArtifactKind,
    PipelineStepStatus,
    PipelineStepType,
)
from app.models.base import TimestampedModel


class GitHubPipelineRunORM(TimestampedModel):
    __tablename__ = "github_pipeline_runs"
    __table_args__ = (
        Index("ix_github_pipeline_runs_created_at", "created_at"),
        Index("ix_github_pipeline_runs_index_job_id", "index_job_id"),
        Index("ix_github_pipeline_runs_review_run_id", "review_run_id"),
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    revision_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("github_pull_request_revisions.id", ondelete="CASCADE"),
        nullable=False,
    )
    head_sha: Mapped[str] = mapped_column(Text, nullable=False)
    index_mode: Mapped[GitHubIndexMode] = mapped_column(String(length=32), nullable=False)
    index_job_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("github_index_jobs.id", ondelete="SET NULL"),
        nullable=True,
    )
    review_run_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("github_review_runs.id", ondelete="SET NULL"),
        nullable=True,
    )
    publish_job_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("github_publish_jobs.id", ondelete="SET NULL"),
        nullable=True,
    )

    steps: Mapped[list[GitHubPipelineStepORM]] = relationship(
        back_populates="pipeline_run",
        cascade="all, delete-orphan",
    )


class GitHubPipelineStepORM(TimestampedModel):
    __tablename__ = "github_pipeline_steps"

    pipeline_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("github_pipeline_runs.id", ondelete="CASCADE"),
        nullable=False,
    )
    step_type: Mapped[PipelineStepType] = mapped_column(String(length=32), nullable=False)
    status: Mapped[PipelineStepStatus] = mapped_column(
        String(length=32),
        nullable=False,
        default=PipelineStepStatus.pending,
        server_default=PipelineStepStatus.pending.value,
    )
    duration_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    model_provider: Mapped[str | None] = mapped_column(String(length=64), nullable=True)
    model_id: Mapped[str | None] = mapped_column(String(length=128), nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error: Mapped[str | None] = mapped_column(Text, nullable=True)

    pipeline_run: Mapped[GitHubPipelineRunORM] = relationship(back_populates="steps")
    artifacts: Mapped[list[GitHubPipelineArtifactORM]] = relationship(
        back_populates="step",
        cascade="all, delete-orphan",
    )


class GitHubPipelineArtifactORM(TimestampedModel):
    __tablename__ = "github_pipeline_artifacts"
    __table_args__ = (
        CheckConstraint(
            "content_text IS NOT NULL OR content_json IS NOT NULL",
            name="ck_github_pipeline_artifacts_content_present",
        ),
    )

    step_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("github_pipeline_steps.id", ondelete="CASCADE"),
        nullable=False,
    )
    kind: Mapped[PipelineArtifactKind] = mapped_column(String(length=32), nullable=False)
    content_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(length=64), nullable=True)

    step: Mapped[GitHubPipelineStepORM] = relationship(back_populates="artifacts")
