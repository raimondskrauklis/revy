# backend/app/models/github_installation.py
"""GitHub App installation — REVY_PRODUCT_SLICE.md."""
from __future__ import annotations

import uuid
from typing import Any

from sqlalchemy import BigInteger, ForeignKey, String, Text, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.enums import GitHubAccountType, GitHubInstallationStatus
from app.models.base import TimestampedModel


class GitHubInstallationORM(TimestampedModel):
    __tablename__ = "github_installations"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workspaces.id"),
        nullable=False,
    )
    github_installation_id: Mapped[int] = mapped_column(BigInteger, nullable=False, unique=True)
    account_login: Mapped[str] = mapped_column(Text, nullable=False)
    account_type: Mapped[GitHubAccountType] = mapped_column(
        String(length=32),
        nullable=False,
    )
    account_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    status: Mapped[GitHubInstallationStatus] = mapped_column(
        String(length=32),
        nullable=False,
        default=GitHubInstallationStatus.active,
        server_default=GitHubInstallationStatus.active.value,
    )
    permissions_snapshot: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
