# backend/app/schemas/github_pipeline.py
"""GitHub pipeline trace API contracts — review-quality O."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.constants.enums import (
    GitHubIndexMode,
    PipelineArtifactKind,
    PipelineStepStatus,
    PipelineStepType,
)


class PipelineArtifactResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    kind: PipelineArtifactKind
    content_text: str | None = None
    content_json: dict[str, Any] | None = None
    content_hash: str | None = None
    created_at: datetime


class PipelineStepResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    step_type: PipelineStepType
    status: PipelineStepStatus
    duration_ms: int | None = None
    model_provider: str | None = None
    model_id: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    error: str | None = None
    created_at: datetime
    updated_at: datetime
    artifacts: list[PipelineArtifactResponse] = Field(default_factory=list)


class PipelineRunResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    workspace_id: UUID
    revision_id: UUID
    head_sha: str
    index_mode: GitHubIndexMode
    index_job_id: UUID | None = None
    review_run_id: UUID | None = None
    publish_job_id: UUID | None = None
    created_at: datetime
    updated_at: datetime
    steps: list[PipelineStepResponse] = Field(default_factory=list)
