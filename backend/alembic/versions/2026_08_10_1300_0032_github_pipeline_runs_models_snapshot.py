# backend/alembic/versions/2026_08_10_1300_0032_github_pipeline_runs_models_snapshot.py
"""github_pipeline_runs.models_snapshot JSONB."""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import JSONB

from alembic import op

revision = "2026_08_10_1300_0032_github_pipeline_runs_models_snapshot"
down_revision = "2026_08_10_1200_0031_pipeline_observability"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "github_pipeline_runs",
        sa.Column("models_snapshot", JSONB, nullable=True),
    )


def downgrade() -> None:
    op.drop_column("github_pipeline_runs", "models_snapshot")
