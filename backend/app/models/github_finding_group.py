# backend/app/models/github_finding_group.py
"""GitHub reconciled finding groups — R5."""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Text, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.enums import (
    FindingCategory,
    FindingSeverity,
    GitHubFindingGroupState,
    ResolutionMethod,
    ResolutionStatus,
)
from app.models.base import TimestampedModel


class GitHubFindingGroupORM(TimestampedModel):
    __tablename__ = "github_finding_groups"
    __table_args__ = (
        UniqueConstraint("pull_request_id", "fingerprint", name="uq_github_finding_groups_pr_fingerprint"),
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workspaces.id"),
        nullable=False,
    )
    pull_request_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("github_pull_requests.id"),
        nullable=False,
    )
    fingerprint: Mapped[str] = mapped_column(String(length=64), nullable=False)
    state: Mapped[GitHubFindingGroupState] = mapped_column(
        String(length=32),
        nullable=False,
        default=GitHubFindingGroupState.active,
        server_default=GitHubFindingGroupState.active.value,
    )
    severity: Mapped[FindingSeverity] = mapped_column(String(length=32), nullable=False)
    category: Mapped[FindingCategory] = mapped_column(String(length=32), nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    file_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    last_seen_revision_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("github_pull_request_revisions.id"),
        nullable=False,
    )
    resolution_status: Mapped[ResolutionStatus | None] = mapped_column(String(length=32), nullable=True)
    resolution_method: Mapped[ResolutionMethod | None] = mapped_column(String(length=32), nullable=True)
    resolved_at_revision_id: Mapped[uuid.UUID | None] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("github_pull_request_revisions.id", ondelete="SET NULL"),
        nullable=True,
    )
    closure_blocked_reason: Mapped[str | None] = mapped_column(Text, nullable=True)
