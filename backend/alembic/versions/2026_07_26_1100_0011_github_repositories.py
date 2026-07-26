# backend/alembic/versions/2026_07_26_1100_0011_github_repositories.py
"""github_repositories — installation-linked repo metadata (R1)."""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "2026_07_26_1100_0011_github_repositories"
down_revision = "2026_07_26_1000_0010_github_webhook_deliveries"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "github_repositories",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            nullable=False,
            server_default=sa.text("uuid_generate_v7()"),
        ),
        sa.Column("installation_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("github_repository_id", sa.BigInteger(), nullable=False),
        sa.Column("name", sa.Text(), nullable=False),
        sa.Column("full_name", sa.Text(), nullable=False),
        sa.Column("default_branch", sa.Text(), nullable=True),
        sa.Column("private", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("html_url", sa.Text(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="active"),
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
        sa.ForeignKeyConstraint(["installation_id"], ["github_installations.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.UniqueConstraint(
            "installation_id",
            "github_repository_id",
            name="uq_github_repositories_installation_repo",
        ),
    )
    op.create_index(
        "ix_github_repositories_workspace_id",
        "github_repositories",
        ["workspace_id"],
    )
    op.create_index(
        "ix_github_repositories_installation_id_status",
        "github_repositories",
        ["installation_id", "status"],
    )


def downgrade() -> None:
    op.drop_index("ix_github_repositories_installation_id_status", table_name="github_repositories")
    op.drop_index("ix_github_repositories_workspace_id", table_name="github_repositories")
    op.drop_table("github_repositories")
