# backend/app/schemas/github_publish.py
"""GitHub publish API contracts — R6."""
from __future__ import annotations

from datetime import datetime
from typing import Any
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
    inline_comments_posted: bool
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    pr_resolution_rollup: dict | None = None

    @classmethod
    def from_publish_job(cls, job: Any) -> GitHubPublishJobResponse:
        response = cls.model_validate(job)
        if response.pr_resolution_rollup is not None:
            return response
        summary_json = getattr(job, "summary_json", None)
        if not isinstance(summary_json, dict):
            return response
        rollup = summary_json.get("pr_resolution_rollup")
        if not isinstance(rollup, dict):
            return response
        return response.model_copy(update={"pr_resolution_rollup": rollup})
