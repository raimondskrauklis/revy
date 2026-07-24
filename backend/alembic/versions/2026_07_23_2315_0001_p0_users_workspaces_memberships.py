# backend/alembic/versions/2026_07_23_2315_0001_p0_users_workspaces_memberships.py
"""users, workspaces, workspace_memberships."""
from __future__ import annotations

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

revision = "2026_07_23_2315_0001_p0_users_workspaces_memberships"
down_revision = None
branch_labels = None
depends_on = None

_UUID_V7_FUNCTION = """
CREATE OR REPLACE FUNCTION uuid_generate_v7()
RETURNS uuid
AS $$
DECLARE
    unix_ts_ms bytea;
    uuid_bytes bytea;
BEGIN
    unix_ts_ms = substring(int8send(floor(extract(epoch from clock_timestamp()) * 1000)::bigint) from 3);
    uuid_bytes = unix_ts_ms || gen_random_bytes(10);
    uuid_bytes = set_byte(uuid_bytes, 6, (get_byte(uuid_bytes, 6) & 15) | 112);
    uuid_bytes = set_byte(uuid_bytes, 8, (get_byte(uuid_bytes, 8) & 63) | 128);
    RETURN encode(uuid_bytes, 'hex')::uuid;
END;
$$ LANGUAGE plpgsql VOLATILE;
"""


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto;")
    op.execute("DROP FUNCTION IF EXISTS uuid_generate_v7();")
    op.execute(_UUID_V7_FUNCTION)

    user_role = postgresql.ENUM("admin", "operator", "viewer", name="user_role", create_type=False)
    user_status = postgresql.ENUM(
        "pending_activation",
        "pending_email_verification",
        "pending_profile",
        "pending_approval",
        "active",
        "rejected",
        "suspended",
        name="user_status",
        create_type=False,
    )
    workspace_status = postgresql.ENUM("active", "suspended", name="workspace_status", create_type=False)
    platform_role = postgresql.ENUM("super_admin", name="platform_role", create_type=False)

    bind = op.get_bind()
    user_role.create(bind, checkfirst=True)
    user_status.create(bind, checkfirst=True)
    workspace_status.create(bind, checkfirst=True)
    platform_role.create(bind, checkfirst=True)

    op.create_table(
        "users",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("uuid_generate_v7()"),
        ),
        sa.Column("keycloak_user_id", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("full_name", sa.String(length=255), nullable=True),
        sa.Column("status", user_status, nullable=False),
        sa.Column("platform_role", platform_role, nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("keycloak_user_id", name="uq_users_keycloak_user_id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )

    op.create_table(
        "workspaces",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("uuid_generate_v7()"),
        ),
        sa.Column("slug", sa.String(length=128), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("status", workspace_status, nullable=False, server_default="active"),
        sa.Column("plan", sa.String(length=64), nullable=True),
        sa.Column("stripe_customer_id", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("slug", name="uq_workspaces_slug"),
    )

    op.create_table(
        "workspace_memberships",
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            primary_key=True,
            nullable=False,
            server_default=sa.text("uuid_generate_v7()"),
        ),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("workspace_id", postgresql.UUID(as_uuid=True), sa.ForeignKey("workspaces.id"), nullable=False),
        sa.Column("role", user_role, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("user_id", "workspace_id", name="uq_workspace_memberships_user_workspace"),
    )


def downgrade() -> None:
    op.drop_table("workspace_memberships")
    op.drop_table("workspaces")
    op.drop_table("users")

    bind = op.get_bind()
    postgresql.ENUM(name="platform_role").drop(bind, checkfirst=True)
    postgresql.ENUM(name="workspace_status").drop(bind, checkfirst=True)
    postgresql.ENUM(name="user_status").drop(bind, checkfirst=True)
    postgresql.ENUM(name="user_role").drop(bind, checkfirst=True)

    op.execute("DROP FUNCTION IF EXISTS uuid_generate_v7();")
