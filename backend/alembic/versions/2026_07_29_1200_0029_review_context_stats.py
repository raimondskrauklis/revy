# backend/alembic/versions/2026_07_29_1200_0029_review_context_stats.py
"""github_review_runs context_stats JSONB."""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "2026_07_29_1200_0029_review_context_stats"
down_revision = "2026_07_28_1200_0028_finding_resolution_closure"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "github_review_runs",
        sa.Column("context_stats", JSONB, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("github_review_runs", "context_stats")
