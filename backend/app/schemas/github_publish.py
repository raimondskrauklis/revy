# backend/app/schemas/github_publish.py
"""GitHub publish API contracts — R6."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, model_validator

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

    @model_validator(mode="before")
    @classmethod
    def _extract_pr_resolution_rollup(cls, data: object) -> object:
        if isinstance(data, dict):
            summary = data.get("summary_json")
            if "pr_resolution_rollup" not in data and isinstance(summary, dict):
                data = {**data, "pr_resolution_rollup": summary.get("pr_resolution_rollup")}
            return data
        summary_json = getattr(data, "summary_json", None)
        if isinstance(summary_json, dict):
            rollup = summary_json.get("pr_resolution_rollup")
            if isinstance(rollup, dict):
                return {
                    "id": data.id,
                    "review_run_id": data.review_run_id,
                    "revision_id": data.revision_id,
                    "workspace_id": data.workspace_id,
                    "head_sha": data.head_sha,
                    "status": data.status,
                    "github_check_run_id": data.github_check_run_id,
                    "github_comment_id": data.github_comment_id,
                    "inline_comments_posted": data.inline_comments_posted,
                    "error_message": data.error_message,
                    "created_at": data.created_at,
                    "updated_at": data.updated_at,
                    "pr_resolution_rollup": rollup,
                }
        return data
