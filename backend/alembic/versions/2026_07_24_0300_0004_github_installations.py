# backend/alembic/versions/2026_07_24_0300_0004_github_installations.py
"""github_installations table."""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "2026_07_24_0300_0004_github_installations"
down_revision = "2026_07_24_0200_0003_invitations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "github_installations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("uuid_generate_v7()"),
        ),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("github_installation_id", sa.BigInteger(), nullable=False),
        sa.Column("account_login", sa.Text(), nullable=False),
        sa.Column("account_type", sa.String(length=32), nullable=False),
        sa.Column("account_id", sa.BigInteger(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("permissions_snapshot", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("github_installation_id", name="uq_github_installations_github_installation_id"),
    )
    op.create_index("ix_github_installations_workspace_id", "github_installations", ["workspace_id"])
    op.create_index(
        "ix_github_installations_workspace_cursor",
        "github_installations",
        ["workspace_id", sa.text("created_at DESC"), sa.text("id DESC")],
    )


def downgrade() -> None:
    op.drop_index("ix_github_installations_workspace_cursor", table_name="github_installations")
    op.drop_index("ix_github_installations_workspace_id", table_name="github_installations")
    op.drop_table("github_installations")
