# backend/app/schemas/github_pull_request.py
"""GitHub pull request API contracts — R2 PR ingestion."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, field_validator

from app.constants.enums import GitHubPullRequestState


class GitHubPullRequestResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    repository_id: UUID
    workspace_id: UUID
    installation_id: UUID
    github_pull_request_id: int
    number: int
    title: str
    state: GitHubPullRequestState
    merged: bool = False
    head_sha: str
    head_ref: str
    base_ref: str
    html_url: str | None
    revision_count: int
    latest_revision_id: UUID | None = None
    created_at: datetime
    updated_at: datetime

    @field_validator("merged", mode="before")
    @classmethod
    def coerce_merged(cls, value: object) -> bool:
        return value is True
