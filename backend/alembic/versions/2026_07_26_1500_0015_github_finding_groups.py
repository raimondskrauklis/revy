# backend/alembic/versions/2026_07_26_1500_0015_github_finding_groups.py
"""github_finding_groups + judge outcomes — R5 reconciliation."""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "2026_07_26_1500_0015_github_finding_groups"
down_revision = "2026_07_26_1400_0014_github_review_runs"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "github_finding_groups",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            nullable=False,
            server_default=sa.text("uuid_generate_v7()"),
        ),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("pull_request_id", sa.Uuid(), nullable=False),
        sa.Column("fingerprint", sa.String(length=64), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False, server_default="active"),
        sa.Column("severity", sa.String(length=32), nullable=False),
        sa.Column("category", sa.String(length=32), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("message", sa.Text(), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=True),
        sa.Column("last_seen_revision_id", sa.Uuid(), nullable=False),
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
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.ForeignKeyConstraint(["pull_request_id"], ["github_pull_requests.id"]),
        sa.ForeignKeyConstraint(["last_seen_revision_id"], ["github_pull_request_revisions.id"]),
        sa.UniqueConstraint("pull_request_id", "fingerprint", name="uq_github_finding_groups_pr_fingerprint"),
    )
    op.create_index("ix_github_finding_groups_pull_request_id", "github_finding_groups", ["pull_request_id"])

    op.create_table(
        "github_finding_judge_outcomes",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            nullable=False,
            server_default=sa.text("uuid_generate_v7()"),
        ),
        sa.Column("group_id", sa.Uuid(), nullable=False),
        sa.Column("review_run_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("outcome", sa.String(length=32), nullable=False),
        sa.Column("judge_notes", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(["group_id"], ["github_finding_groups.id"]),
        sa.ForeignKeyConstraint(["review_run_id"], ["github_review_runs.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
    )
    op.create_index(
        "ix_github_finding_judge_outcomes_review_run_id",
        "github_finding_judge_outcomes",
        ["review_run_id"],
    )

    op.add_column("github_findings", sa.Column("group_id", sa.Uuid(), nullable=True))
    op.create_foreign_key(
        "fk_github_findings_group_id",
        "github_findings",
        "github_finding_groups",
        ["group_id"],
        ["id"],
    )
    op.create_index("ix_github_findings_group_id", "github_findings", ["group_id"])


def downgrade() -> None:
    op.drop_index("ix_github_findings_group_id", table_name="github_findings")
    op.drop_constraint("fk_github_findings_group_id", "github_findings", type_="foreignkey")
    op.drop_column("github_findings", "group_id")
    op.drop_index(
        "ix_github_finding_judge_outcomes_review_run_id",
        table_name="github_finding_judge_outcomes",
    )
    op.drop_table("github_finding_judge_outcomes")
    op.drop_index("ix_github_finding_groups_pull_request_id", table_name="github_finding_groups")
    op.drop_table("github_finding_groups")
