# backend/alembic/versions/2026_07_26_1300_0013_github_indexing.py
"""github_index_jobs + github_code_chunks — R3 indexing."""
from __future__ import annotations

import sqlalchemy as sa
from pgvector.sqlalchemy import Vector

from alembic import op

revision = "2026_07_26_1300_0013_github_indexing"
down_revision = "2026_07_26_1200_0012_github_pull_requests"
branch_labels = None
depends_on = None

EMBEDDING_DIM = 512


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    op.create_table(
        "github_index_jobs",
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
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("chunk_count", sa.Integer(), nullable=True),
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
    op.create_index("ix_github_index_jobs_revision_id", "github_index_jobs", ["revision_id"])

    op.create_table(
        "github_code_chunks",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            nullable=False,
            server_default=sa.text("uuid_generate_v7()"),
        ),
        sa.Column("index_job_id", sa.Uuid(), nullable=False),
        sa.Column("revision_id", sa.Uuid(), nullable=False),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("file_path", sa.Text(), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("embedding", Vector(EMBEDDING_DIM), nullable=True),
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
        sa.ForeignKeyConstraint(["index_job_id"], ["github_index_jobs.id"]),
        sa.ForeignKeyConstraint(["revision_id"], ["github_pull_request_revisions.id"]),
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"]),
        sa.UniqueConstraint(
            "revision_id",
            "file_path",
            "chunk_index",
            name="uq_github_code_chunks_revision_file_chunk",
        ),
    )
    op.create_index("ix_github_code_chunks_revision_id", "github_code_chunks", ["revision_id"])


def downgrade() -> None:
    op.drop_index("ix_github_code_chunks_revision_id", table_name="github_code_chunks")
    op.drop_table("github_code_chunks")
    op.drop_index("ix_github_index_jobs_revision_id", table_name="github_index_jobs")
    op.drop_table("github_index_jobs")
