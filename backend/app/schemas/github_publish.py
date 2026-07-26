# backend/app/schemas/github_publish.py
"""GitHub publish API contracts — R6."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.constants.enums import GitHubPublishJobStatus


class GitHubPublishJobResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    review_run_id: UUID
    revision_id: UUID
    workspace_id: UUID
    head_sha: str
    status: GitHubPublishJobStatus
    github_check_run_id: int | None
    github_comment_id: int | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime
