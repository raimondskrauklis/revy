# backend/alembic/versions/2026_07_26_2200_0023_workspace_model_policies.py
"""workspace_model_policies — MODEL_POLICY M2."""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "2026_07_26_2200_0023_workspace_model_policies"
down_revision = "2026_07_26_2100_0022_review_run_and_judge_model_metadata"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "workspace_model_policies",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            nullable=False,
            server_default=sa.text("uuid_generate_v7()"),
        ),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=64), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("model_id", sa.String(length=128), nullable=False),
        sa.Column("region", sa.String(length=64), nullable=True),
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
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.UniqueConstraint("workspace_id", "role", name="uq_workspace_model_policies_workspace_role"),
    )
    op.create_index(
        "ix_workspace_model_policies_workspace_id",
        "workspace_model_policies",
        ["workspace_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_workspace_model_policies_workspace_id", table_name="workspace_model_policies")
    op.drop_table("workspace_model_policies")
