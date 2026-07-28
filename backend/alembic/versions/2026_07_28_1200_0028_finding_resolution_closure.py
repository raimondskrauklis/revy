# backend/alembic/versions/2026_07_28_1200_0028_finding_resolution_closure.py
"""github_finding_groups closure columns; judge_purpose on outcomes."""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "2026_07_28_1200_0028_finding_resolution_closure"
down_revision = "2026_07_28_1000_0027_github_pull_request_body"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "github_finding_groups",
        sa.Column("resolution_method", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "github_finding_groups",
        sa.Column("resolved_at_revision_id", sa.Uuid(), nullable=True),
    )
    op.add_column(
        "github_finding_groups",
        sa.Column("closure_blocked_reason", sa.Text(), nullable=True),
    )
    op.create_foreign_key(
        "fk_github_finding_groups_resolved_at_revision_id",
        "github_finding_groups",
        "github_pull_request_revisions",
        ["resolved_at_revision_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.add_column(
        "github_finding_judge_outcomes",
        sa.Column(
            "judge_purpose",
            sa.String(length=32),
            nullable=False,
            server_default="discovery",
        ),
    )


def downgrade() -> None:
    op.drop_column("github_finding_judge_outcomes", "judge_purpose")
    op.drop_constraint(
        "fk_github_finding_groups_resolved_at_revision_id",
        "github_finding_groups",
        type_="foreignkey",
    )
    op.drop_column("github_finding_groups", "closure_blocked_reason")
    op.drop_column("github_finding_groups", "resolved_at_revision_id")
    op.drop_column("github_finding_groups", "resolution_method")
