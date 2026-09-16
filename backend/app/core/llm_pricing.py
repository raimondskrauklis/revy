# backend/app/core/llm_pricing.py
"""Static LLM price table — pipeline observability (estimated cost in P3)."""
from __future__ import annotations

from dataclasses import dataclass
from decimal import Decimal


@dataclass(frozen=True, slots=True)
class LlmPrice:
    input_usd_per_1k: Decimal
    output_usd_per_1k: Decimal


# Placeholder rates — informational only until PO-Q12 vendor APIs.
_LLM_PRICING: dict[tuple[str, str], LlmPrice] = {
    ("moonshot", "kimi-k2.7-code"): LlmPrice(Decimal("0.003"), Decimal("0.015")),
    ("rtu", "kimi-k2.7-code"): LlmPrice(Decimal("0.003"), Decimal("0.015")),
    ("anthropic", "claude-sonnet-4-20250514"): LlmPrice(Decimal("0.003"), Decimal("0.015")),
    ("voyage", "voyage-3"): LlmPrice(Decimal("0.0001"), Decimal("0")),
}


def lookup_price(provider: str, model_id: str) -> LlmPrice | None:
    key = (provider, model_id)
    priced = _LLM_PRICING.get(key)
    if priced is not None:
        return priced
    basename = model_id.rsplit("/", 1)[-1]
    if basename == model_id:
        return None
    return _LLM_PRICING.get((provider, basename))
