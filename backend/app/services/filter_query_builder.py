# backend/app/services/filter_query_builder.py
"""Scope JSON → SQL filters — extend per SEARCH.md."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from typing import Any
from uuid import UUID

from app.services.search.fts import build_tsquery, normalize_search_text


@dataclass
class FilterSpec:
    """Validated filter dimensions for scope queries (saved search, export, investigation)."""

    entity_type: str
    q: str | None = None
    date_range: dict[str, str] | None = None
    statuses: list[str] | None = None
    workspace_id: UUID | None = None

    @classmethod
    def from_raw(cls, raw: dict[str, Any], *, workspace_id: UUID | None) -> FilterSpec:
        return cls(
            entity_type=str(raw["entity_type"]),
            q=raw.get("q"),
            date_range=raw.get("date_range"),
            statuses=raw.get("statuses"),
            workspace_id=workspace_id,
        )


class FilterQueryBuilder:
    """Compose SQLAlchemy filters — subclass per product entity."""

    def __init__(self, spec: FilterSpec) -> None:
        self.spec = spec

    def build(self):
        raise NotImplementedError("Wire to your ORM model in the product repo")

    def _apply_q_filter(self, query, *, search_vector_col, reference_col):
        q = self.spec.q
        if not q:
            return query
        normalized = normalize_search_text(q)
        tsquery = build_tsquery(normalized)
        # Prefer: reference ILIKE OR search_vector @@ to_tsquery('simple_unaccent', :tsquery)
        _ = (tsquery, reference_col, search_vector_col)
        return query

    def _apply_date_range(self, query, *, date_col):
        dr = self.spec.date_range
        if not dr:
            return query
        if dr.get("from"):
            query = query.where(date_col >= date.fromisoformat(dr["from"]))
        if dr.get("to"):
            query = query.where(date_col <= date.fromisoformat(dr["to"]))
        return query

    def _apply_tenancy(self, query, *, workspace_col):
        if self.spec.workspace_id is not None:
            query = query.where(workspace_col == self.spec.workspace_id)
        return query
