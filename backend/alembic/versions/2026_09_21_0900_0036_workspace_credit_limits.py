# backend/alembic/versions/2026_09_21_0900_0036_workspace_credit_limits.py
"""workspaces completed_review_runs + review_run_limit."""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "2026_09_21_0900_0036_workspace_credit_limits"
down_revision = "2026_09_19_2200_0035_finding_group_claim_slot"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "workspaces",
        sa.Column("completed_review_runs", sa.Integer(), nullable=False, server_default="0"),
    )
    op.add_column(
        "workspaces",
        sa.Column("review_run_limit", sa.Integer(), nullable=True),
    )

    # Backfill existing workspaces
    op.execute("UPDATE workspaces SET review_run_limit = 25 WHERE plan IS NULL OR plan = 'free'")
    op.execute("UPDATE workspaces SET review_run_limit = NULL WHERE plan = 'pro'")


def downgrade() -> None:
    op.drop_column("workspaces", "review_run_limit")
    op.drop_column("workspaces", "completed_review_runs")