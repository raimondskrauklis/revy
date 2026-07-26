# backend/app/models/github_review_run.py
"""GitHub review runs — R4."""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, Integer, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.enums import GitHubReviewJudgeStatus, GitHubReviewRunStatus, ReviewProfile
from app.models.base import TimestampedModel


class GitHubReviewRunORM(TimestampedModel):
    __tablename__ = "github_review_runs"

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
    status: Mapped[GitHubReviewRunStatus] = mapped_column(
        String(length=32),
        nullable=False,
        default=GitHubReviewRunStatus.pending,
        server_default=GitHubReviewRunStatus.pending.value,
    )
    profile: Mapped[ReviewProfile] = mapped_column(
        String(length=32),
        nullable=False,
        default=ReviewProfile.standard,
        server_default=ReviewProfile.standard.value,
    )
    provider: Mapped[str | None] = mapped_column(String(length=32), nullable=True)
    model_id: Mapped[str | None] = mapped_column(String(length=128), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    judge_escalation_candidate_count: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=0,
        server_default="0",
    )
    judge_status: Mapped[GitHubReviewJudgeStatus] = mapped_column(
        String(length=32),
        nullable=False,
        default=GitHubReviewJudgeStatus.not_applicable,
        server_default=GitHubReviewJudgeStatus.not_applicable.value,
    )
