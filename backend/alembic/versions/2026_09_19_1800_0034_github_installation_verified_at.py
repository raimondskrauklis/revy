# backend/alembic/versions/2026_09_19_1800_0034_github_installation_verified_at.py
"""github_installations.verified_at + grandfather backfill."""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "2026_09_19_1800_0034_github_installation_verified_at"
down_revision = "2026_09_16_2100_0033_github_pull_request_merged"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "github_installations",
        sa.Column("verified_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.execute(
        sa.text(
            "UPDATE github_installations "
            "SET verified_at = created_at "
            "WHERE status = 'active' AND verified_at IS NULL"
        )
    )


def downgrade() -> None:
    op.drop_column("github_installations", "verified_at")
