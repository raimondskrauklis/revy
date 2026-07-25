# backend/alembic/versions/2026_07_25_2340_0009_impersonation_sessions.py
"""impersonation_sessions table."""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "2026_07_25_2340_0009_impersonation_sessions"
down_revision = "2026_07_25_2330_0008_lifecycle_export_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "impersonation_sessions",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("uuid_generate_v7()"),
        ),
        sa.Column(
            "actor_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column(
            "target_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("reason", sa.Text(), nullable=False),
        sa.Column(
            "started_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column("ended_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_index(
        "uq_impersonation_sessions_actor_active",
        "impersonation_sessions",
        ["actor_user_id"],
        unique=True,
        postgresql_where=sa.text("ended_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index(
        "uq_impersonation_sessions_actor_active",
        table_name="impersonation_sessions",
    )
    op.drop_table("impersonation_sessions")
