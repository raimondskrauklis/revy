# backend/alembic/versions/2026_07_26_1600_0016_github_publish_jobs.py
"""github_publish_jobs — R6 GitHub publish."""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "2026_07_26_1600_0016_github_publish_jobs"
down_revision = "2026_07_26_1500_0015_github_finding_groups"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "github_publish_jobs",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            nullable=False,
            server_default=sa.text("uuid_generate_v7()"),
        ),
        sa.Column("review_run_id", sa.Uuid(), nullable=False),
        sa.Column("revision_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("head_sha", sa.Text(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("github_check_run_id", sa.BigInteger(), nullable=True),
        sa.Column("github_comment_id", sa.BigInteger(), nullable=True),
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
        sa.ForeignKeyConstraint(["review_run_id"], ["github_review_runs.id"]),
        sa.ForeignKeyConstraint(["revision_id"], ["github_pull_request_revisions.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
    )
    op.create_index("ix_github_publish_jobs_review_run_id", "github_publish_jobs", ["review_run_id"])
    op.create_index("ix_github_publish_jobs_head_sha", "github_publish_jobs", ["head_sha"])
    op.create_index(
        "ix_github_publish_jobs_workspace_id_revision_id",
        "github_publish_jobs",
        ["workspace_id", "revision_id"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_github_publish_jobs_workspace_id_revision_id",
        table_name="github_publish_jobs",
    )
    op.drop_index("ix_github_publish_jobs_head_sha", table_name="github_publish_jobs")
    op.drop_index("ix_github_publish_jobs_review_run_id", table_name="github_publish_jobs")
    op.drop_table("github_publish_jobs")
