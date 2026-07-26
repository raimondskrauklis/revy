# backend/app/models/github_webhook_delivery.py
"""GitHub webhook delivery idempotency — one row per X-GitHub-Delivery UUID."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import BigInteger, DateTime, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utc_now


class GitHubWebhookDeliveryORM(Base):
    __tablename__ = "github_webhook_deliveries"

    delivery_id: Mapped[str] = mapped_column(Text, primary_key=True, nullable=False)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    installation_id: Mapped[int | None] = mapped_column(BigInteger, nullable=True)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=text("NOW()"),
    )
