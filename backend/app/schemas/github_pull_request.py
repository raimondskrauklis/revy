# backend/app/schemas/github_pull_request.py
"""GitHub pull request API contracts — R2 PR ingestion."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

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
    head_sha: str
    head_ref: str
    base_ref: str
    html_url: str | None
    revision_count: int
    latest_revision_id: UUID | None = None
    created_at: datetime
    updated_at: datetime
