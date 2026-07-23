# backend/app/core/alembic_postgresql.py
"""PostgreSQL DDL impl — long ``alembic_version.version_num`` for KP-style revision ids."""
from __future__ import annotations

from typing import Any

from alembic.ddl.postgresql import PostgresqlImpl
from sqlalchemy import Column, MetaData, PrimaryKeyConstraint, String, Table

# Default Alembic uses VARCHAR(32); our rev ids are YYYY_MM_DD_HHMM_NNNN_slug (~50+ chars).
ALEMBIC_VERSION_NUM_LENGTH = 128


class RevyPostgresqlImpl(PostgresqlImpl):
    __dialect__ = "postgresql"

    def version_table_impl(
        self,
        version_table: str,
        version_table_schema: str | None,
        version_table_pk: bool,
        **kw: Any,
    ) -> Table:
        vt = Table(
            version_table,
            MetaData(),
            Column(
                "version_num",
                String(ALEMBIC_VERSION_NUM_LENGTH),
                nullable=False,
            ),
            schema=version_table_schema,
        )
        if version_table_pk:
            vt.append_constraint(
                PrimaryKeyConstraint(
                    "version_num",
                    name=f"{version_table}_pkc",
                )
            )
        return vt
