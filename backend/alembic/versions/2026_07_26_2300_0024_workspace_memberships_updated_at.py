# backend/alembic/versions/2026_07_26_2300_0024_workspace_memberships_updated_at.py
"""workspace_memberships updated_at — align with TimestampedModel."""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "2026_07_26_2300_0024_workspace_memberships_updated_at"
down_revision = "2026_07_26_2200_0023_workspace_model_policies"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "workspace_memberships",
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )
    op.execute("UPDATE workspace_memberships SET updated_at = created_at")


def downgrade() -> None:
    op.drop_column("workspace_memberships", "updated_at")
