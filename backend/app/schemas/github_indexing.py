# backend/app/schemas/github_indexing.py
"""GitHub indexing API contracts — R3."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from app.constants.enums import GitHubIndexJobStatus


class GitHubIndexJobResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    revision_id: UUID
    workspace_id: UUID
    status: GitHubIndexJobStatus
    error_message: str | None
    chunk_count: int | None
    created_at: datetime
    updated_at: datetime


class GitHubCodeChunkResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    revision_id: UUID
    file_path: str
    chunk_index: int
    content: str
    created_at: datetime


class GitHubCodeChunkListResponse(BaseModel):
    items: list[GitHubCodeChunkResponse]
    offset: int
    limit: int
    has_more: bool


class GitHubChunkSearchRequest(BaseModel):
    query: str = Field(min_length=1, max_length=2000)
    top_k: int = Field(default=10, ge=1, le=50)


class GitHubChunkSearchResult(BaseModel):
    id: UUID
    file_path: str
    chunk_index: int
    content: str
    score: float
