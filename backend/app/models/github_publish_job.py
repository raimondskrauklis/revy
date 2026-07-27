# backend/app/models/github_publish_job.py
"""GitHub publish jobs — R6."""
from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, ForeignKey, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.enums import GitHubPublishJobStatus
from app.models.base import TimestampedModel


class GitHubPublishJobORM(TimestampedModel):
    __tablename__ = "github_publish_jobs"

    review_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("github_review_runs.id"),
        nullable=False,
    )
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
    head_sha: Mapped[str] = mapped_column(Text, nullable=False)
    status: Mapped[GitHubPublishJobStatus] = mapped_column(
        String(length=32),
        nullable=False,
        default=GitHubPublishJobStatus.pending,
        server_default=GitHubPublishJobStatus.pending.value,
    )
    github_check_run_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    github_comment_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    inline_comments_posted: Mapped[bool] = mapped_column(nullable=False, default=False, server_default="false")
    summary_json: Mapped[dict | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
