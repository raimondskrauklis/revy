# backend/alembic/versions/2026_07_27_1200_0026_review_quality.py
"""review quality schema — pipeline trace, diff index, resolution metrics."""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "2026_07_27_1200_0026_review_quality"
down_revision = "2026_07_27_0000_0025_findings_suggestion_review_judge_status"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("github_pull_request_revisions", sa.Column("base_sha", sa.Text(), nullable=True))

    op.add_column(
        "github_index_jobs",
        sa.Column("index_mode", sa.String(length=32), nullable=True),
    )
    op.execute(sa.text("UPDATE github_index_jobs SET index_mode = 'full'"))
    op.alter_column(
        "github_index_jobs",
        "index_mode",
        nullable=False,
        server_default="diff",
    )
    op.add_column("github_index_jobs", sa.Column("fallback_reason", sa.Text(), nullable=True))
    op.add_column("github_index_jobs", sa.Column("warning_message", sa.Text(), nullable=True))
    op.add_column(
        "github_index_jobs",
        sa.Column("index_incremental", sa.Boolean(), nullable=False, server_default="true"),
    )

    op.add_column("github_code_chunks", sa.Column("content_hash", sa.String(length=64), nullable=True))
    op.add_column("github_findings", sa.Column("evidence_snippet", sa.Text(), nullable=True))
    op.add_column("github_finding_groups", sa.Column("resolution_status", sa.String(length=32), nullable=True))
    op.add_column(
        "github_publish_jobs",
        sa.Column("summary_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )

    op.create_table(
        "github_pipeline_runs",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            nullable=False,
            server_default=sa.text("uuid_generate_v7()"),
        ),
        sa.Column("workspace_id", sa.Uuid(), nullable=False),
        sa.Column("revision_id", sa.Uuid(), nullable=False),
        sa.Column("head_sha", sa.Text(), nullable=False),
        sa.Column("index_mode", sa.String(length=32), nullable=False),
        sa.Column("index_job_id", sa.Uuid(), nullable=True),
        sa.Column("review_run_id", sa.Uuid(), nullable=True),
        sa.Column("publish_job_id", sa.Uuid(), nullable=True),
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
        sa.ForeignKeyConstraint(["workspace_id"], ["workspaces.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(
            ["revision_id"],
            ["github_pull_request_revisions.id"],
            ondelete="CASCADE",
        ),
        sa.ForeignKeyConstraint(
            ["index_job_id"],
            ["github_index_jobs.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["review_run_id"],
            ["github_review_runs.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["publish_job_id"],
            ["github_publish_jobs.id"],
            ondelete="SET NULL",
        ),
    )
    op.create_index("ix_github_pipeline_runs_workspace_id", "github_pipeline_runs", ["workspace_id"])
    op.create_index("ix_github_pipeline_runs_revision_id", "github_pipeline_runs", ["revision_id"])
    op.create_index("ix_github_pipeline_runs_created_at", "github_pipeline_runs", ["created_at"])
    op.create_index(
        "ix_github_pipeline_runs_workspace_id_revision_id",
        "github_pipeline_runs",
        ["workspace_id", "revision_id"],
    )

    op.create_table(
        "github_pipeline_steps",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            nullable=False,
            server_default=sa.text("uuid_generate_v7()"),
        ),
        sa.Column("pipeline_run_id", sa.Uuid(), nullable=False),
        sa.Column("step_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("model_provider", sa.String(length=64), nullable=True),
        sa.Column("model_id", sa.String(length=128), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("error", sa.Text(), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["pipeline_run_id"],
            ["github_pipeline_runs.id"],
            ondelete="CASCADE",
        ),
    )
    op.create_index(
        "ix_github_pipeline_steps_pipeline_run_id",
        "github_pipeline_steps",
        ["pipeline_run_id"],
    )

    op.create_table(
        "github_pipeline_artifacts",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            nullable=False,
            server_default=sa.text("uuid_generate_v7()"),
        ),
        sa.Column("step_id", sa.Uuid(), nullable=False),
        sa.Column("kind", sa.String(length=32), nullable=False),
        sa.Column("content_text", sa.Text(), nullable=True),
        sa.Column("content_json", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column("content_hash", sa.String(length=64), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["step_id"],
            ["github_pipeline_steps.id"],
            ondelete="CASCADE",
        ),
        sa.CheckConstraint(
            "content_text IS NOT NULL OR content_json IS NOT NULL",
            name="ck_github_pipeline_artifacts_content_present",
        ),
    )
    op.create_index(
        "ix_github_pipeline_artifacts_step_id",
        "github_pipeline_artifacts",
        ["step_id"],
    )


def downgrade() -> None:
    op.drop_index("ix_github_pipeline_artifacts_step_id", table_name="github_pipeline_artifacts")
    op.drop_table("github_pipeline_artifacts")
    op.drop_index("ix_github_pipeline_steps_pipeline_run_id", table_name="github_pipeline_steps")
    op.drop_table("github_pipeline_steps")
    op.drop_index("ix_github_pipeline_runs_created_at", table_name="github_pipeline_runs")
    op.drop_index(
        "ix_github_pipeline_runs_workspace_id_revision_id",
        table_name="github_pipeline_runs",
    )
    op.drop_index("ix_github_pipeline_runs_revision_id", table_name="github_pipeline_runs")
    op.drop_index("ix_github_pipeline_runs_workspace_id", table_name="github_pipeline_runs")
    op.drop_table("github_pipeline_runs")

    op.drop_column("github_publish_jobs", "summary_json")
    op.drop_column("github_finding_groups", "resolution_status")
    op.drop_column("github_findings", "evidence_snippet")
    op.drop_column("github_code_chunks", "content_hash")
    op.drop_column("github_index_jobs", "index_incremental")
    op.drop_column("github_index_jobs", "warning_message")
    op.drop_column("github_index_jobs", "fallback_reason")
    op.drop_column("github_index_jobs", "index_mode")
    op.drop_column("github_pull_request_revisions", "base_sha")
