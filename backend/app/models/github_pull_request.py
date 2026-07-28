# backend/app/models/github_pull_request.py
"""GitHub pull request metadata — R2 PR ingestion."""
from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import BigInteger, Boolean, DateTime, ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.enums import GitHubPullRequestState
from app.models.base import TimestampedModel


class GitHubPullRequestORM(TimestampedModel):
    __tablename__ = "github_pull_requests"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("github_repositories.id"),
        nullable=False,
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workspaces.id"),
        nullable=False,
    )
    installation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("github_installations.id"),
        nullable=False,
    )
    github_pull_request_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    number: Mapped[int] = mapped_column(Integer, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[GitHubPullRequestState] = mapped_column(
        String(length=32),
        nullable=False,
        default=GitHubPullRequestState.open,
        server_default=GitHubPullRequestState.open.value,
    )
    head_sha: Mapped[str] = mapped_column(Text, nullable=False)
    head_ref: Mapped[str] = mapped_column(Text, nullable=False)
    base_ref: Mapped[str] = mapped_column(Text, nullable=False)
    html_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    body: Mapped[str | None] = mapped_column(Text, nullable=True)
    revision_count: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    is_draft: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default="false",
    )


class GitHubPullRequestRevisionORM(TimestampedModel):
    __tablename__ = "github_pull_request_revisions"

    pull_request_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("github_pull_requests.id"),
        nullable=False,
    )
    revision_number: Mapped[int] = mapped_column(Integer, nullable=False)
    head_sha: Mapped[str] = mapped_column(Text, nullable=False)
    base_sha: Mapped[str | None] = mapped_column(Text, nullable=True)


class GitHubPullRequestReviewORM(TimestampedModel):
    __tablename__ = "github_pull_request_reviews"

    pull_request_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("github_pull_requests.id"),
        nullable=False,
    )
    github_review_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    author_login: Mapped[str] = mapped_column(Text, nullable=False)
    state: Mapped[str] = mapped_column(String(length=32), nullable=False)
    submitted_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
