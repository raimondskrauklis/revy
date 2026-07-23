# backend/app/models/base.py
"""ORM base classes — see internal-docs starter-pack docs/backend/MODEL_BASES.md."""
from __future__ import annotations

from datetime import UTC, datetime
from uuid import UUID

from sqlalchemy import DateTime, event, text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def utc_now() -> datetime:
    """Return the current UTC datetime (timezone-aware).

    Use this everywhere Python sets a timestamp — ORM defaults, soft delete,
    service-layer writes. Do not use naive ``datetime.now()`` or local timezone.

    PostgreSQL ``NOW()`` is UTC when the DB timezone is configured correctly;
    Python-side defaults must still be explicit via this helper.
    """
    return datetime.now(UTC)


class Base(DeclarativeBase):
    """Root declarative base — concrete tables inherit TimestampedModel or AuditableModel."""


class TimestampedModel(Base):
    """Base model with UUIDv7 primary key and ``created_at`` / ``updated_at``.

    Use for identity tables, junction rows, and immutable reference data.
    P0 examples: ``users``, ``workspaces``, ``workspace_memberships``.

    Do not use ``AuditableModel`` for those P0 tables — they use status enums
    or hard deletes instead of ``deleted_at`` (MODEL_BASES.md).
    """

    __abstract__ = True

    id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        primary_key=True,
        server_default=text("uuid_generate_v7()"),
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=text("NOW()"),
        comment="Record creation timestamp (UTC)",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=text("NOW()"),
        comment="Record last update timestamp (UTC)",
    )


@event.listens_for(TimestampedModel, "before_update", propagate=True)
def _touch_updated_at(_mapper, _connection, target: TimestampedModel) -> None:
    """Keep ``updated_at`` in sync on every ORM update — always via ``utc_now()``."""
    target.updated_at = utc_now()


class AuditableModel(TimestampedModel):
    """Timestamped model with actor audit fields and soft delete (``deleted_at``).

    Use for tenant-owned product rows users create, edit, or delete in the UI
    (e.g. repositories, findings). List queries must filter ``deleted_at IS NULL``
    (see ``app.core.query_filters.active_only`` when that module exists).

    Do **not** use for ``users`` or ``workspaces`` — account/workspace lifecycle
    uses status enums, not soft delete.
    """

    __abstract__ = True

    created_by_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        nullable=True,
        comment="User who created this record",
    )
    updated_by_id: Mapped[UUID | None] = mapped_column(
        PgUUID(as_uuid=True),
        nullable=True,
        comment="User who last updated this record",
    )
    deleted_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        comment="Soft delete timestamp (UTC); set via ``soft_delete()`` only",
    )

    @property
    def is_deleted(self) -> bool:
        """True when ``deleted_at`` is set to a timestamp."""
        deleted_at = self.__dict__.get("deleted_at")
        if deleted_at is None and "deleted_at" not in self.__dict__:
            deleted_at = getattr(self, "deleted_at", None)
        return isinstance(deleted_at, datetime)

    def soft_delete(self, *, deleted_by_id: UUID | None = None) -> None:
        """Mark the row deleted without removing it from the database.

        Args:
            deleted_by_id: Dashboard user performing the delete (audit trail).
        """
        self.deleted_at = utc_now()
        if deleted_by_id is not None:
            self.updated_by_id = deleted_by_id

    def restore(self, *, restored_by_id: UUID | None = None) -> None:
        """Clear soft delete and optionally record who restored the row.

        Args:
            restored_by_id: Dashboard user performing the restore.
        """
        self.deleted_at = None
        if restored_by_id is not None:
            self.updated_by_id = restored_by_id


__all__ = ["AuditableModel", "Base", "TimestampedModel", "utc_now"]
