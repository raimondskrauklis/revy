# backend/app/models/github_repository.py
"""GitHub repository metadata — R1 repository sync."""
from __future__ import annotations

import uuid

from sqlalchemy import BigInteger, Boolean, ForeignKey, String, Text, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.enums import GitHubRepositoryStatus
from app.models.base import TimestampedModel


class GitHubRepositoryORM(TimestampedModel):
    __tablename__ = "github_repositories"

    installation_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("github_installations.id"),
        nullable=False,
    )
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workspaces.id"),
        nullable=False,
    )
    github_repository_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    full_name: Mapped[str] = mapped_column(Text, nullable=False)
    default_branch: Mapped[str | None] = mapped_column(Text, nullable=True)
    private: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    html_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    status: Mapped[GitHubRepositoryStatus] = mapped_column(
        String(length=32),
        nullable=False,
        default=GitHubRepositoryStatus.active,
        server_default=GitHubRepositoryStatus.active.value,
    )
