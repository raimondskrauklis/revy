# backend/alembic/versions/2026_07_26_1200_0012_github_pull_requests.py
"""github_pull_requests, revisions, reviews — R2 PR ingestion."""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "2026_07_26_1200_0012_github_pull_requests"
down_revision = "2026_07_26_1100_0011_github_repositories"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "github_pull_requests",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            nullable=False,
            server_default=sa.text("uuid_generate_v7()"),
        ),
        sa.Column("repository_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("installation_id", sa.Uuid(), nullable=False),
        sa.Column("github_pull_request_id", sa.BigInteger(), nullable=False),
        sa.Column("number", sa.Integer(), nullable=False),
        sa.Column("title", sa.Text(), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False, server_default="open"),
        sa.Column("head_sha", sa.Text(), nullable=False),
        sa.Column("head_ref", sa.Text(), nullable=False),
        sa.Column("base_ref", sa.Text(), nullable=False),
        sa.Column("html_url", sa.Text(), nullable=True),
        sa.Column("revision_count", sa.Integer(), nullable=False, server_default="1"),
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
        sa.ForeignKeyConstraint(["repository_id"], ["github_repositories.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.ForeignKeyConstraint(["installation_id"], ["github_installations.id"]),
        sa.UniqueConstraint(
            "repository_id",
            "github_pull_request_id",
            name="uq_github_pull_requests_repository_pr",
        ),
    )
    op.create_index(
        "ix_github_pull_requests_workspace_id",
        "github_pull_requests",
        ["workspace_id"],
    )
    op.create_index(
        "ix_github_pull_requests_repository_id_state",
        "github_pull_requests",
        ["repository_id", "state"],
    )

    op.create_table(
        "github_pull_request_revisions",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            nullable=False,
            server_default=sa.text("uuid_generate_v7()"),
        ),
        sa.Column("pull_request_id", sa.Uuid(), nullable=False),
        sa.Column("revision_number", sa.Integer(), nullable=False),
        sa.Column("head_sha", sa.Text(), nullable=False),
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
        sa.ForeignKeyConstraint(["pull_request_id"], ["github_pull_requests.id"]),
        sa.UniqueConstraint(
            "pull_request_id",
            "revision_number",
            name="uq_github_pr_revisions_pr_number",
        ),
    )

    op.create_table(
        "github_pull_request_reviews",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            nullable=False,
            server_default=sa.text("uuid_generate_v7()"),
        ),
        sa.Column("pull_request_id", sa.Uuid(), nullable=False),
        sa.Column("github_review_id", sa.BigInteger(), nullable=False),
        sa.Column("author_login", sa.Text(), nullable=False),
        sa.Column("state", sa.String(length=32), nullable=False),
        sa.Column("submitted_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(["pull_request_id"], ["github_pull_requests.id"]),
        sa.UniqueConstraint("github_review_id", name="uq_github_pull_request_reviews_github_id"),
    )


def downgrade() -> None:
    op.drop_table("github_pull_request_reviews")
    op.drop_table("github_pull_request_revisions")
    op.drop_index("ix_github_pull_requests_repository_id_state", table_name="github_pull_requests")
    op.drop_index("ix_github_pull_requests_workspace_id", table_name="github_pull_requests")
    op.drop_table("github_pull_requests")
