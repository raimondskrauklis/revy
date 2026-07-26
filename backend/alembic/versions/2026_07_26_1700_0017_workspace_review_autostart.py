# backend/alembic/versions/2026_07_26_1700_0017_workspace_review_autostart.py
"""workspace review_autostart + index job trigger_source — R8 automation."""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "2026_07_26_1700_0017_workspace_review_autostart"
down_revision = "2026_07_26_1600_0016_github_publish_jobs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "workspaces",
        sa.Column(
            "review_autostart_enabled",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("true"),
        ),
    )
    op.add_column(
        "github_index_jobs",
        sa.Column(
            "trigger_source",
            sa.String(length=32),
            nullable=False,
            server_default="manual",
        ),
    )


def downgrade() -> None:
    op.drop_column("github_index_jobs", "trigger_source")
    op.drop_column("workspaces", "review_autostart_enabled")
