# backend/app/models/workspace_model_policy.py
"""Per-workspace model policy overrides — MODEL_POLICY M2."""

from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import TimestampedModel


class WorkspaceModelPolicyORM(TimestampedModel):
    __tablename__ = "workspace_model_policies"
    __table_args__ = (
        UniqueConstraint("workspace_id", "role", name="uq_workspace_model_policies_workspace_role"),
    )

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workspaces.id"),
        nullable=False,
    )
    role: Mapped[str] = mapped_column(String(length=64), nullable=False)
    provider: Mapped[str] = mapped_column(String(length=32), nullable=False)
    model_id: Mapped[str] = mapped_column(String(length=128), nullable=False)
    region: Mapped[str | None] = mapped_column(String(length=64), nullable=True)
