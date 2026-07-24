# backend/alembic/versions/2026_07_23_2315_0002_p1_items.py
"""items table."""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "2026_07_23_2315_0002_p1_items"
down_revision = "2026_07_23_2315_0001_p0_users_workspaces_memberships"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "items",
        sa.Column("id", sa.Uuid(), server_default=sa.text("uuid_generate_v7()"), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", sa.String(length=32), server_default="draft", nullable=False),
        sa.Column("created_by_id", sa.Uuid(), nullable=True),
        sa.Column("updated_by_id", sa.Uuid(), nullable=True),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("NOW()"), nullable=False),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_items_workspace_id", "items", ["workspace_id"])
    op.create_index(
        "ix_items_workspace_cursor",
        "items",
        ["workspace_id", sa.text("created_at DESC"), sa.text("id DESC")],
        postgresql_where=sa.text("deleted_at IS NULL"),
    )


def downgrade() -> None:
    op.drop_index("ix_items_workspace_cursor", table_name="items")
    op.drop_index("ix_items_workspace_id", table_name="items")
    op.drop_table("items")
