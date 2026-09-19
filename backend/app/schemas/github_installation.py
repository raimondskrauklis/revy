# backend/app/schemas/github_installation.py
"""GitHub installation API contracts — REVY_PRODUCT_SLICE.md."""
from __future__ import annotations

from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field

from app.constants.enums import GitHubAccountType, GitHubInstallationStatus


class GitHubInstallationCreate(BaseModel):
    github_installation_id: int = Field(gt=0)
    account_login: str = Field(min_length=1, max_length=255)
    account_type: GitHubAccountType
    account_id: int = Field(gt=0)
    permissions_snapshot: dict[str, Any] | None = None


class GitHubInstallationResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: UUID
    workspace_id: UUID
    github_installation_id: int
    account_login: str
    account_type: GitHubAccountType
    account_id: int
    status: GitHubInstallationStatus
    permissions_snapshot: dict[str, Any] | None
    verified_at: datetime | None
    created_at: datetime
    updated_at: datetime
