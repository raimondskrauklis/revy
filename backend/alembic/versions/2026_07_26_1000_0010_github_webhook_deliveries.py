# backend/alembic/versions/2026_07_26_1000_0010_github_webhook_deliveries.py
"""github_webhook_deliveries — GitHub webhook idempotency (R0)."""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "2026_07_26_1000_0010_github_webhook_deliveries"
down_revision = "2026_07_25_2340_0009_impersonation_sessions"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "github_webhook_deliveries",
        sa.Column("delivery_id", sa.Text(), primary_key=True, nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column("installation_id", sa.BigInteger(), nullable=True),
        sa.Column("payload_json", JSONB(), nullable=False),
        sa.Column(
            "received_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )


def downgrade() -> None:
    op.drop_table("github_webhook_deliveries")
