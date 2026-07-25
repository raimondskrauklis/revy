# backend/app/models/data_export_job.py
"""User data export jobs — ACCOUNT_LIFECYCLE.md."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, DateTime, Enum, ForeignKey, Text
from sqlalchemy.dialects.postgresql import UUID as PgUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.enums import ExportJobStatus
from app.models.base import TimestampedModel


class DataExportJobORM(TimestampedModel):
    __tablename__ = "data_export_jobs"

    user_id: Mapped[UUID] = mapped_column(
        PgUUID(as_uuid=True),
        ForeignKey("users.id"),
        nullable=False,
    )
    status: Mapped[ExportJobStatus] = mapped_column(
        Enum(ExportJobStatus, name="export_job_status", native_enum=True),
        nullable=False,
        default=ExportJobStatus.pending,
    )
    storage_key: Mapped[str | None] = mapped_column(Text, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    file_size_bytes: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
