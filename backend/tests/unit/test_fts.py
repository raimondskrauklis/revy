# backend/tests/unit/test_fts.py
"""Unit tests for search normalization — extend per SEARCH.md."""
from app.services.search.fts import build_tsquery, normalize_search_text


def test_normalize_search_text_smart_quotes():
    assert normalize_search_text("“hello”") == '"hello"'


def test_build_tsquery_prefix_for_long_tokens():
    assert build_tsquery("widget panel") == "widget:* & panel:*"


def test_build_tsquery_empty_returns_none():
    assert build_tsquery("   ") is None
