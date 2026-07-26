# backend/alembic/env.py
"""Alembic environment — async migrations against DATABASE_URL from app settings."""
import os
import re
from datetime import UTC, datetime
from logging.config import fileConfig
from pathlib import Path

from sqlalchemy import inspect, pool, text
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

import app.core.alembic_postgresql
import app.models  # noqa: F401 — register ORM tables on Base.metadata
from alembic import context
from app.core.alembic_postgresql import ALEMBIC_VERSION_NUM_LENGTH
from app.core.config import settings
from app.models.base import Base

config = context.config

# CI / local test DB: alembic -x test=true upgrade head
test_mode = context.get_x_argument(as_dictionary=True).get("test", "").lower() == "true"
if test_mode:
    db_url = os.environ.get("TEST_DATABASE_URL") or (
        str(settings.test_database_url) if settings.test_database_url else None
    )
    if not db_url:
        raise ValueError("TEST_DATABASE_URL required for test mode (backend/.env)")
else:
    db_url = str(settings.database_url)

config.set_main_option("sqlalchemy.url", db_url)

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata

# KP-style descriptive migration filenames (alembic.ini: file_template = %%(rev)s):
#   YYYY_MM_DD_HHMM_NNNN_slug.py
# Example: 2025_11_17_1522_0001_uuid_v7_base_setup.py
#            |date |time|seq | message slug from -m |
_MIGRATION_SLUG_RE = re.compile(r"[^a-z0-9_]+")


def normalize_migration_slug(message: str) -> str:
    """Turn ``alembic revision -m "..."`` into a stable filename slug."""
    slug = message.strip().lower().replace(" ", "_").replace("-", "_")
    slug = _MIGRATION_SLUG_RE.sub("", slug)
    slug = re.sub(r"_+", "_", slug).strip("_")
    return slug or "migration"


def get_next_migration_sequence() -> int:
    """Next 4-digit sequence (NNNN) from ``versions/`` — index 4 in the filename stem."""
    versions_dir = Path(__file__).parent / "versions"
    if not versions_dir.exists():
        return 1

    max_seq = 0
    for path in versions_dir.glob("*.py"):
        if path.name in ("__init__.py",) or path.name.startswith("."):
            continue

        stem = path.name
        while stem.lower().endswith(".py"):
            stem = stem[:-3]

        parts = stem.split("_")
        # YYYY_MM_DD_HHMM_NNNN_slug...
        if len(parts) < 5:
            continue

        seq_part = parts[4]
        if len(seq_part) == 4 and seq_part.isdigit():
            max_seq = max(max_seq, int(seq_part))

    return max_seq + 1 if max_seq else 1


def build_migration_revision_id(message: str, *, now: datetime | None = None) -> str:
    """Build revision id + filename stem: ``YYYY_MM_DD_HHMM_NNNN_slug``."""
    ts = now or datetime.now(UTC)
    date_str = ts.strftime("%Y_%m_%d_%H%M")
    seq = get_next_migration_sequence()
    slug = normalize_migration_slug(message)
    return f"{date_str}_{seq:04d}_{slug}"


def widen_alembic_version_column(connection: Connection) -> None:
    """Upgrade legacy Alembic default ``version_num VARCHAR(32)`` if table exists."""
    if "alembic_version" not in inspect(connection).get_table_names():
        return

    for column in inspect(connection).get_columns("alembic_version"):
        if column["name"] != "version_num":
            continue
        col_type = column["type"]
        length = getattr(col_type, "length", None)
        if length is not None and length < ALEMBIC_VERSION_NUM_LENGTH:
            connection.execute(
                text(
                    f"ALTER TABLE alembic_version "
                    f"ALTER COLUMN version_num TYPE VARCHAR({ALEMBIC_VERSION_NUM_LENGTH})"
                )
            )
        break


def process_revision_directives(context, revision, directives):
    if not directives:
        return
    msg = getattr(context.config.cmd_opts, "message", None) or "migration"
    directives[0].rev_id = build_migration_revision_id(msg)


def do_run_migrations(connection: Connection) -> None:
    widen_alembic_version_column(connection)
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        process_revision_directives=process_revision_directives,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.execution_options(isolation_level="AUTOCOMMIT")
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    import asyncio

    asyncio.run(run_async_migrations())


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        process_revision_directives=process_revision_directives,
    )
    with context.begin_transaction():
        context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
