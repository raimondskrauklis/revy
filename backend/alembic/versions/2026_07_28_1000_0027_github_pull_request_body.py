# backend/alembic/versions/2026_07_28_1000_0027_github_pull_request_body.py
"""github_pull_requests.body — Moonshot reviewer PR description (J-4)."""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "2026_07_28_1000_0027_github_pull_request_body"
down_revision = "2026_07_27_1200_0026_review_quality"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column("github_pull_requests", sa.Column("body", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("github_pull_requests", "body")
