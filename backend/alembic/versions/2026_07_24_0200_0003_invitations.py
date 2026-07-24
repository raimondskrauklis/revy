# backend/alembic/versions/2026_07_24_0200_0003_invitations.py
"""workspace_invitations table."""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "2026_07_24_0200_0003_invitations"
down_revision = "2026_07_23_2315_0002_p1_items"
branch_labels = None
depends_on = None


def upgrade() -> None:
    user_role = postgresql.ENUM("admin", "operator", "viewer", name="user_role", create_type=False)

    op.create_table(
        "workspace_invitations",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("uuid_generate_v7()"),
        ),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("email", sa.Text(), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("token", sa.Text(), nullable=False),
        sa.Column(
            "invited_by_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("accepted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("token", name="uq_workspace_invitations_token"),
    )
    op.create_index(
        "ix_workspace_invitations_email",
        "workspace_invitations",
        [sa.text("lower(email)")],
    )


def downgrade() -> None:
    op.drop_index("ix_workspace_invitations_email", table_name="workspace_invitations")
    op.drop_table("workspace_invitations")
