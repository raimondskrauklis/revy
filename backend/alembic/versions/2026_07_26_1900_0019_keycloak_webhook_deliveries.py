# backend/alembic/versions/2026_07_26_1900_0019_keycloak_webhook_deliveries.py
"""keycloak_webhook_deliveries — Keycloak identity webhook idempotency."""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "2026_07_26_1900_0019_keycloak_webhook_deliveries"
down_revision = "2026_07_26_1800_0018_github_pull_request_is_draft"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "keycloak_webhook_deliveries",
        sa.Column("delivery_id", sa.Text(), nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("payload_json", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("NOW()"),
            nullable=False,
        ),
        sa.PrimaryKeyConstraint("delivery_id"),
    )


def downgrade() -> None:
    op.drop_table("keycloak_webhook_deliveries")
