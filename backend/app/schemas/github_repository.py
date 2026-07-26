# backend/app/schemas/github_repository.py
"""GitHub repository API contracts — R1 repository sync."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from app.constants.enums import GitHubRepositoryStatus


class GitHubRepositoryResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    installation_id: UUID
    workspace_id: UUID
    github_repository_id: int
    name: str
    full_name: str
    default_branch: str | None
    private: bool
    html_url: str | None
    status: GitHubRepositoryStatus
    created_at: datetime
    updated_at: datetime
