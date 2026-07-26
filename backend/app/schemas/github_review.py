# backend/app/schemas/github_review.py
"""GitHub review API contracts — R4."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.constants.enums import (
    FindingCategory,
    FindingSeverity,
    GitHubFindingGroupState,
    GitHubReviewRunStatus,
    ReviewProfile,
)


class ReviewTriggerRequest(BaseModel):
    profile: ReviewProfile = ReviewProfile.standard


class GitHubReviewRunResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    revision_id: UUID
    workspace_id: UUID
    status: GitHubReviewRunStatus
    profile: ReviewProfile
    provider: str | None
    error_message: str | None
    created_at: datetime
    updated_at: datetime


class GitHubFindingResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    review_run_id: UUID
    severity: FindingSeverity
    category: FindingCategory
    title: str
    message: str
    file_path: str | None
    start_line: int | None
    end_line: int | None
    created_at: datetime


class GitHubFindingListResponse(BaseModel):
    items: list[GitHubFindingResponse]
    offset: int
    limit: int
    has_more: bool


class ReconciledFindingResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    pull_request_id: UUID
    state: GitHubFindingGroupState
    severity: FindingSeverity
    category: FindingCategory
    title: str
    message: str
    file_path: str | None
    last_seen_revision_id: UUID
    created_at: datetime
    updated_at: datetime
