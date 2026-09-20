# backend/alembic/versions/2026_09_19_2200_0035_finding_group_claim_slot.py
"""github_finding_groups start_line + claim_slot."""
from __future__ import annotations

import hashlib

import sqlalchemy as sa

from alembic import op

revision = "2026_09_19_2200_0035_finding_group_claim_slot"
down_revision = "2026_09_19_1800_0034_github_installation_verified_at"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "github_finding_groups",
        sa.Column("start_line", sa.Integer(), nullable=True),
    )
    op.add_column(
        "github_finding_groups",
        sa.Column("claim_slot", sa.String(length=64), nullable=True),
    )
    conn = op.get_bind()
    rows = conn.execute(
        sa.text(
            """
            SELECT DISTINCT ON (group_id) group_id, start_line, title
            FROM github_findings
            WHERE group_id IS NOT NULL
            ORDER BY group_id, created_at DESC
            """
        )
    )
    for group_id, start_line, title in rows:
        claim_slot = hashlib.sha256((title or "").strip().encode("utf-8")).hexdigest()[:32]
        conn.execute(
            sa.text(
                "UPDATE github_finding_groups "
                "SET start_line = :start_line, claim_slot = :claim_slot "
                "WHERE id = :id"
            ),
            {"start_line": start_line, "claim_slot": claim_slot, "id": group_id},
        )


def downgrade() -> None:
    op.drop_column("github_finding_groups", "claim_slot")
    op.drop_column("github_finding_groups", "start_line")
