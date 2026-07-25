# backend/alembic/versions/2026_07_25_2330_0008_lifecycle_export_jobs.py
"""lifecycle deleted enums and data_export_jobs table."""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "2026_07_25_2330_0008_lifecycle_export_jobs"
down_revision = "2026_07_25_2300_0007_stripe_webhook_events"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.execute("ALTER TYPE user_status ADD VALUE IF NOT EXISTS 'deleted'")
    op.execute("ALTER TYPE workspace_status ADD VALUE IF NOT EXISTS 'deleted'")

    export_job_status = postgresql.ENUM(
        "pending",
        "processing",
        "completed",
        "failed",
        name="export_job_status",
        create_type=False,
    )
    bind = op.get_bind()
    export_job_status.create(bind, checkfirst=True)

    op.create_table(
        "data_export_jobs",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("uuid_generate_v7()"),
        ),
        sa.Column(
            "user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("status", export_job_status, nullable=False),
        sa.Column("storage_key", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("file_size_bytes", sa.BigInteger(), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("NOW()"),
        ),
    )
    op.create_index(
        "ix_data_export_jobs_user_id_status",
        "data_export_jobs",
        ["user_id", "status"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_data_export_jobs_user_id_status", table_name="data_export_jobs")
    op.drop_table("data_export_jobs")
    op.execute("DROP TYPE IF EXISTS export_job_status")
