# backend/app/models/github_finding_judge_outcome.py
"""GitHub finding judge outcomes — R5."""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.enums import GitHubJudgeOutcome
from app.models.base import TimestampedModel


class GitHubFindingJudgeOutcomeORM(TimestampedModel):
    __tablename__ = "github_finding_judge_outcomes"

    group_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("github_finding_groups.id"),
        nullable=False,
    )
    review_run_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("github_review_runs.id"),
        nullable=False,
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workspaces.id"),
        nullable=False,
    )
    outcome: Mapped[GitHubJudgeOutcome] = mapped_column(String(length=32), nullable=False)
    judge_provider: Mapped[str | None] = mapped_column(String(length=32), nullable=True)
    judge_model_id: Mapped[str | None] = mapped_column(String(length=128), nullable=True)
    judge_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
