# backend/app/models/github_pipeline.py
"""GitHub pipeline trace — review-quality explainability (O)."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.enums import (
    GitHubIndexMode,
    PipelineArtifactKind,
    PipelineStepStatus,
    PipelineStepType,
)
from app.models.base import TimestampedModel


class GitHubPipelineRunORM(TimestampedModel):
    __tablename__ = "github_pipeline_runs"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workspaces.id", ondelete="CASCADE"),
        nullable=False,
    )
    revision_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("github_pull_request_revisions.id"),
        nullable=False,
    )
    head_sha: Mapped[str] = mapped_column(Text, nullable=False)
    index_mode: Mapped[GitHubIndexMode] = mapped_column(String(length=32), nullable=False)
    index_job_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("github_index_jobs.id"),
        nullable=True,
    )
    review_run_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("github_review_runs.id"),
        nullable=True,
    )
    publish_job_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("github_publish_jobs.id"),
        nullable=True,
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


class GitHubPipelineArtifactORM(TimestampedModel):
    __tablename__ = "github_pipeline_artifacts"

    step_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("github_pipeline_steps.id", ondelete="CASCADE"),
        nullable=False,
    )
    kind: Mapped[PipelineArtifactKind] = mapped_column(String(length=32), nullable=False)
    content_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    content_json: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    content_hash: Mapped[str | None] = mapped_column(String(length=64), nullable=True)
