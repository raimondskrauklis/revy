# backend/app/schemas/github_publish.py
"""GitHub publish API contracts — R6."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, ModelWrapValidatorHandler, model_validator

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

    @model_validator(mode="wrap")
    @classmethod
    def _inject_rollup_from_summary_json(
        cls,
        data: Any,
        handler: ModelWrapValidatorHandler[GitHubPublishJobResponse],
    ) -> GitHubPublishJobResponse:
        model = handler(data)
        if model.pr_resolution_rollup is not None:
            return model
        summary_json = (
            data.get("summary_json") if isinstance(data, dict) else getattr(data, "summary_json", None)
        )
        if not isinstance(summary_json, dict):
            return model
        rollup = summary_json.get("pr_resolution_rollup")
        if not isinstance(rollup, dict):
            return model
        return model.model_copy(update={"pr_resolution_rollup": rollup})
