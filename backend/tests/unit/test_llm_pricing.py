# backend/tests/unit/test_llm_pricing.py
"""Pipeline observability P0 — llm_pricing config."""
from decimal import Decimal

from app.core.llm_pricing import lookup_price


def test_lookup_price_known_model():
    price = lookup_price("moonshot", "kimi-k2.7-code")
    assert price is not None
    assert price.input_usd_per_1k == Decimal("0.003")


def test_lookup_price_unknown_returns_none():
    assert lookup_price("unknown", "model") is None
