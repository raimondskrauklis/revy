# backend/app/schemas/github_pipeline.py
"""GitHub pipeline trace API contracts — review-quality O."""
from __future__ import annotations

from datetime import datetime
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
    content_json: dict[str, object] | None = None
    content_hash: str | None = None
    created_at: datetime


class ModelsSnapshotRoleResponse(BaseModel):
    provider: str
    model_id: str
    dimensions: int | None = None


class ModelsSnapshotResponse(BaseModel):
    embedding: ModelsSnapshotRoleResponse | None = None
    reviewer: ModelsSnapshotRoleResponse | None = None
    judge: ModelsSnapshotRoleResponse | None = None
    publish: ModelsSnapshotRoleResponse | None = None


class PipelineStepResponse(BaseModel):
    id: UUID
    step_type: PipelineStepType
    status: PipelineStepStatus
    duration_ms: int | None = None
    model_provider: str | None = None
    model_id: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    error: str | None = None
    embedding_model: str | None = None
    embedding_dimensions: int | None = None
    embedding_skipped_reason: str | None = None
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
    models_snapshot: ModelsSnapshotResponse | None = None
    created_at: datetime
    updated_at: datetime
    steps: list[PipelineStepResponse] = Field(default_factory=list)
