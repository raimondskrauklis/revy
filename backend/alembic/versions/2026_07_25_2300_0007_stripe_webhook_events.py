# backend/alembic/versions/2026_07_25_2300_0007_stripe_webhook_events.py
"""stripe_webhook_events table and workspaces stripe index."""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "2026_07_25_2300_0007_stripe_webhook_events"
down_revision = "2026_07_25_2230_0006_api_audit"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "stripe_webhook_events",
        sa.Column("event_id", sa.Text(), primary_key=True, nullable=False),
        sa.Column("event_type", sa.Text(), nullable=False),
        sa.Column(
            "processed_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index(
        "ix_workspaces_stripe_customer_id",
        "workspaces",
        ["stripe_customer_id"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_workspaces_stripe_customer_id", table_name="workspaces")
    op.drop_table("stripe_webhook_events")
