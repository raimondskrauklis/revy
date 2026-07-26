# backend/alembic/versions/2026_07_26_1400_0014_github_review_runs.py
"""github_review_runs + github_findings — R4 review run."""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "2026_07_26_1400_0014_github_review_runs"
down_revision = "2026_07_26_1300_0013_github_indexing"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "github_review_runs",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            nullable=False,
            server_default=sa.text("uuid_generate_v7()"),
        ),
        sa.Column("revision_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("profile", sa.String(length=32), nullable=False, server_default="standard"),
        sa.Column("provider", sa.String(length=32), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["revision_id"], ["github_pull_request_revisions.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
    )
    op.create_index("ix_github_review_runs_revision_id", "github_review_runs", ["revision_id"])

    op.create_table(
        "github_findings",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            nullable=False,
            server_default=sa.text("uuid_generate_v7()"),
        ),
        sa.Column("review_run_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("start_line", sa.Integer(), nullable=True),
        sa.Column("end_line", sa.Integer(), nullable=True),
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
        sa.ForeignKeyConstraint(["review_run_id"], ["github_review_runs.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
    )
    op.create_index("ix_github_findings_review_run_id", "github_findings", ["review_run_id"])


def downgrade() -> None:
    op.drop_index("ix_github_findings_review_run_id", table_name="github_findings")
    op.drop_table("github_findings")
    op.drop_index("ix_github_review_runs_revision_id", table_name="github_review_runs")
    op.drop_table("github_review_runs")
