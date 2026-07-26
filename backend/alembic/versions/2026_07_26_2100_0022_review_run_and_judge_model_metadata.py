# backend/alembic/versions/2026_07_26_2100_0022_review_run_and_judge_model_metadata.py
"""review run model_id + judge outcome model metadata — MODEL_POLICY M0."""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "2026_07_26_2100_0022_review_run_and_judge_model_metadata"
down_revision = "2026_07_26_1910_0020_keycloak_webhook_deliveries_received_at_idx"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "github_review_runs",
        sa.Column("model_id", sa.String(length=128), nullable=True),
    )
    op.add_column(
        "github_finding_judge_outcomes",
        sa.Column("judge_provider", sa.String(length=32), nullable=True),
    )
    op.add_column(
        "github_finding_judge_outcomes",
        sa.Column("judge_model_id", sa.String(length=128), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("github_finding_judge_outcomes", "judge_model_id")
    op.drop_column("github_finding_judge_outcomes", "judge_provider")
    op.drop_column("github_review_runs", "model_id")
