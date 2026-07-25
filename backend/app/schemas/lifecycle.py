# backend/app/schemas/lifecycle.py
"""Account lifecycle request/response schemas — ACCOUNT_LIFECYCLE.md."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.constants.enums import ExportJobStatus


class DeleteWorkspaceRequest(BaseModel):
    confirm_slug: str = Field(min_length=1, max_length=128)


class DeleteAccountRequest(BaseModel):
    confirm_email: str = Field(min_length=1, max_length=320)


class ExportJobCreateResponse(BaseModel):
    job_id: UUID


class ExportJobStatusResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    status: ExportJobStatus
    created_at: datetime
    completed_at: datetime | None
    expires_at: datetime | None
