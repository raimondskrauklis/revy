# backend/alembic/versions/2026_07_27_0000_0025_findings_suggestion_review_judge_status.py
"""findings suggestion + review run judge status."""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "2026_07_27_0000_0025_findings_suggestion_review_judge_status"
down_revision = "2026_07_26_2300_0024_workspace_memberships_updated_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("github_findings", sa.Column("suggestion", sa.Text(), nullable=True))
    op.add_column(
        "github_review_runs",
        sa.Column(
            "judge_escalation_candidate_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "github_review_runs",
        sa.Column(
            "judge_status",
            sa.String(length=32),
            nullable=False,
            server_default="not_applicable",
        ),
    )


def downgrade() -> None:
    op.drop_column("github_review_runs", "judge_status")
    op.drop_column("github_review_runs", "judge_escalation_candidate_count")
    op.drop_column("github_findings", "suggestion")
