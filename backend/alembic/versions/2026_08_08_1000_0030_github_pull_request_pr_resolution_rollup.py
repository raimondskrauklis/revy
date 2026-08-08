# backend/alembic/versions/2026_08_08_1000_0030_github_pull_request_pr_resolution_rollup.py
"""github_pull_requests.pr_resolution_rollup JSONB — PSR P0."""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "2026_08_08_1000_0030_github_pull_request_pr_resolution_rollup"
down_revision = "2026_07_29_1200_0029_review_context_stats"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "github_pull_requests",
        sa.Column("pr_resolution_rollup", JSONB, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("github_pull_requests", "pr_resolution_rollup")
