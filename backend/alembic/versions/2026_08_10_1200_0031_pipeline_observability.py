# backend/alembic/versions/2026_08_10_1200_0031_pipeline_observability.py
"""github_llm_call_attempts + review run observability columns."""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "2026_08_10_1200_0031_pipeline_observability"
down_revision = "2026_08_08_1000_0030_github_pull_request_pr_resolution_rollup"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "github_llm_call_attempts",
        sa.Column(
            "id",
            sa.Uuid(),
            primary_key=True,
            nullable=False,
            server_default=sa.text("uuid_generate_v7()"),
        ),
        sa.Column("pipeline_run_id", sa.Uuid(), nullable=False),
        sa.Column("review_run_id", sa.Uuid(), nullable=True),
        sa.Column("index_job_id", sa.Uuid(), nullable=True),
        sa.Column("step_type", sa.String(length=32), nullable=False),
        sa.Column("operation_name", sa.String(length=32), nullable=False),
        sa.Column("attempt_no", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("request_model", sa.String(length=128), nullable=False),
        sa.Column("response_model", sa.String(length=128), nullable=True),
        sa.Column("input_tokens", sa.Integer(), nullable=True),
        sa.Column("output_tokens", sa.Integer(), nullable=True),
        sa.Column("finish_reason", sa.String(length=64), nullable=True),
        sa.Column("wait_ms", sa.Integer(), nullable=True),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("failure_class", sa.String(length=32), nullable=True),
        sa.Column("response_preview", sa.String(length=512), nullable=True),
        sa.Column("response_sha256", sa.String(length=64), nullable=True),
        sa.Column("batch_size", sa.Integer(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
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
        sa.ForeignKeyConstraint(
            ["review_run_id"],
            ["github_review_runs.id"],
            ondelete="SET NULL",
        ),
        sa.ForeignKeyConstraint(
            ["index_job_id"],
            ["github_index_jobs.id"],
            ondelete="SET NULL",
        ),
    )
    op.create_index(
        "ix_github_llm_call_attempts_pipeline_run_id",
        "github_llm_call_attempts",
        ["pipeline_run_id"],
    )
    op.create_index(
        "ix_github_llm_call_attempts_review_run_step",
        "github_llm_call_attempts",
        ["review_run_id", "step_type"],
    )
    op.create_index(
        "ix_github_llm_call_attempts_started_at",
        "github_llm_call_attempts",
        ["started_at"],
    )
    op.create_index(
        "ix_github_llm_call_attempts_provider_model",
        "github_llm_call_attempts",
        ["provider", "request_model"],
    )

    op.add_column(
        "github_review_runs",
        sa.Column("timing_stats", JSONB, nullable=True),
    )
    op.add_column(
        "github_review_runs",
        sa.Column("token_rollup", JSONB, nullable=True),
    )
    op.add_column(
        "github_review_runs",
        sa.Column("failure_stage", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "github_review_runs",
        sa.Column("failure_class", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "github_review_runs",
        sa.Column("trigger_source", sa.String(length=32), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("github_review_runs", "trigger_source")
    op.drop_column("github_review_runs", "failure_class")
    op.drop_column("github_review_runs", "failure_stage")
    op.drop_column("github_review_runs", "token_rollup")
    op.drop_column("github_review_runs", "timing_stats")
    op.drop_index(
        "ix_github_llm_call_attempts_provider_model",
        table_name="github_llm_call_attempts",
    )
    op.drop_index(
        "ix_github_llm_call_attempts_started_at",
        table_name="github_llm_call_attempts",
    )
    op.drop_index(
        "ix_github_llm_call_attempts_review_run_step",
        table_name="github_llm_call_attempts",
    )
    op.drop_index(
        "ix_github_llm_call_attempts_pipeline_run_id",
        table_name="github_llm_call_attempts",
    )
    op.drop_table("github_llm_call_attempts")
