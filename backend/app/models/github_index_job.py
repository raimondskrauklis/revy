# backend/app/models/github_index_job.py
"""GitHub index jobs — R3 indexing."""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.enums import GitHubIndexJobStatus, GitHubIndexJobTriggerSource
from app.models.base import TimestampedModel


class GitHubIndexJobORM(TimestampedModel):
    __tablename__ = "github_index_jobs"

    revision_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("github_pull_request_revisions.id"),
        nullable=False,
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workspaces.id"),
        nullable=False,
    )
    status: Mapped[GitHubIndexJobStatus] = mapped_column(
        String(length=32),
        nullable=False,
        default=GitHubIndexJobStatus.pending,
        server_default=GitHubIndexJobStatus.pending.value,
    )
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    chunk_count: Mapped[int | None] = mapped_column(Integer, nullable=True)
    trigger_source: Mapped[GitHubIndexJobTriggerSource] = mapped_column(
        String(length=32),
        nullable=False,
        default=GitHubIndexJobTriggerSource.manual,
        server_default=GitHubIndexJobTriggerSource.manual.value,
    )
