# backend/alembic/versions/2026_07_26_2000_0021_github_code_chunks_embedding_dim.py
"""github_code_chunks embedding vector(1024) for voyage-code-3."""
from __future__ import annotations

from alembic import op

revision = "2026_07_26_2000_0021_github_code_chunks_embedding_dim"
down_revision = "2026_07_26_1910_0020_keycloak_webhook_deliveries_received_at_idx"
branch_labels = None
depends_on = None

OLD_EMBEDDING_DIM = 512
NEW_EMBEDDING_DIM = 1024


def upgrade() -> None:
    # Incompatible vectors must be cleared before widening the column type.
    op.execute("UPDATE github_code_chunks SET embedding = NULL")
    op.execute(
        f"ALTER TABLE github_code_chunks "
        f"ALTER COLUMN embedding TYPE vector({NEW_EMBEDDING_DIM})"
    )


def downgrade() -> None:
    op.execute("UPDATE github_code_chunks SET embedding = NULL")
    op.execute(
        f"ALTER TABLE github_code_chunks "
        f"ALTER COLUMN embedding TYPE vector({OLD_EMBEDDING_DIM})"
    )
