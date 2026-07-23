# backend/app/models/items.py
"""Example P1 tenant model — canonical reference for AGENT_PATTERNS.md."""
from __future__ import annotations

import uuid

from sqlalchemy import ForeignKey, String, Uuid
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.enums import ItemStatus
from app.models.base import AuditableModel


class ItemORM(AuditableModel):
    __tablename__ = "items"

    workspace_id: Mapped[uuid.UUID] = mapped_column(
        Uuid(as_uuid=True),
        ForeignKey("workspaces.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(
        String(32),
        nullable=False,
        default=ItemStatus.draft.value,
        server_default=ItemStatus.draft.value,
    )

    # Alembic: partial index (workspace_id, created_at DESC, id DESC) WHERE deleted_at IS NULL
