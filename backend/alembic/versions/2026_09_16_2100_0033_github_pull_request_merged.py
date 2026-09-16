# backend/alembic/versions/2026_09_16_2100_0033_github_pull_request_merged.py
"""github_pull_requests.merged."""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "2026_09_16_2100_0033_github_pull_request_merged"
down_revision = "2026_08_10_1300_0032_github_pipeline_runs_models_snapshot"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "github_pull_requests",
        sa.Column(
            "merged",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("github_pull_requests", "merged")
