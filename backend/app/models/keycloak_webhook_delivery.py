# backend/app/models/keycloak_webhook_delivery.py
"""Keycloak webhook idempotency — one row per delivery/event id."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from sqlalchemy import DateTime, Text, text
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base, utc_now


class KeycloakWebhookDeliveryORM(Base):
    __tablename__ = "keycloak_webhook_deliveries"

    delivery_id: Mapped[str] = mapped_column(Text, primary_key=True, nullable=False)
    event_type: Mapped[str] = mapped_column(Text, nullable=False)
    payload_json: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    received_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        default=utc_now,
        server_default=text("NOW()"),
    )
