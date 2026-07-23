# backend/app/models/workspaces.py
"""Workspace (tenant) ORM — TimestampedModel; ops state via WorkspaceStatus."""
from __future__ import annotations

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.enums import WorkspaceStatus
from app.models.base import TimestampedModel


class WorkspaceORM(TimestampedModel):
    __tablename__ = "workspaces"

    slug: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[WorkspaceStatus] = mapped_column(
        Enum(WorkspaceStatus, name="workspace_status", native_enum=True),
        nullable=False,
        default=WorkspaceStatus.active,
    )
    plan: Mapped[str | None] = mapped_column(String(64), nullable=True)
    stripe_customer_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
