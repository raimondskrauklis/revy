# backend/app/models/workspace_memberships.py
"""User ↔ workspace role — TimestampedModel; remove row on leave (no soft delete)."""
from __future__ import annotations

import uuid

from sqlalchemy import Enum, ForeignKey, UniqueConstraint, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.enums import AppRole
from app.models.base import TimestampedModel


class WorkspaceMembershipORM(TimestampedModel):
    __tablename__ = "workspace_memberships"
    __table_args__ = (UniqueConstraint("user_id", "workspace_id", name="uq_workspace_memberships_user_workspace"),)

    user_id: Mapped[uuid.UUID] = mapped_column(Uuid(as_uuid=True), ForeignKey("users.id"), nullable=False)
    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workspaces.id"),
        nullable=False,
    )
    role: Mapped[AppRole] = mapped_column(
        Enum(AppRole, name="user_role", native_enum=True),
        nullable=False,
    )
