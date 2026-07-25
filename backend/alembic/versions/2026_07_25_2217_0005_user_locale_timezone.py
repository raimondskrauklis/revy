# backend/alembic/versions/2026_07_25_2217_0005_user_locale_timezone.py
"""users.locale and users.timezone — W1 personal settings."""
from __future__ import annotations

import sqlalchemy as sa

from alembic import op

revision = "2026_07_25_2217_0005_user_locale_timezone"
down_revision = "2026_07_24_0300_0004_github_installations"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "users",
        sa.Column("locale", sa.String(length=16), nullable=False, server_default="en"),
    )
    op.add_column(
        "users",
        sa.Column("timezone", sa.String(length=64), nullable=False, server_default="UTC"),
    )


def downgrade() -> None:
    op.drop_column("users", "timezone")
    op.drop_column("users", "locale")
