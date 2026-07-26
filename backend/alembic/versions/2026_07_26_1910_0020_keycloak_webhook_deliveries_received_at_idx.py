# backend/alembic/versions/2026_07_26_1910_0020_keycloak_webhook_deliveries_received_at_idx.py
"""keycloak_webhook_deliveries received_at index — prune/cleanup queries."""
from __future__ import annotations

from alembic import op

revision = "2026_07_26_1910_0020_keycloak_webhook_deliveries_received_at_idx"
down_revision = "2026_07_26_1900_0019_keycloak_webhook_deliveries"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_index(
        "ix_keycloak_webhook_deliveries_received_at",
        "keycloak_webhook_deliveries",
        ["received_at"],
        if_not_exists=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_keycloak_webhook_deliveries_received_at",
        table_name="keycloak_webhook_deliveries",
        if_exists=True,
    )
