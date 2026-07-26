# backend/alembic/versions/2026_07_26_1800_0018_github_pull_request_is_draft.py
"""github_pull_requests.is_draft — R8 draft PR guard."""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "2026_07_26_1800_0018_github_pull_request_is_draft"
down_revision = "2026_07_26_1700_0017_workspace_review_autostart"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "github_pull_requests",
        sa.Column(
            "is_draft",
            sa.Boolean(),
            nullable=False,
            server_default=sa.text("false"),
        ),
    )


def downgrade() -> None:
    op.drop_column("github_pull_requests", "is_draft")
