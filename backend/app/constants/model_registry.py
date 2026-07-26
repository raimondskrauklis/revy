# backend/app/constants/model_registry.py
"""Known (provider, model_id) catalog — platform defaults and M2 API catalog."""
from __future__ import annotations

from dataclasses import dataclass

from app.constants.model_policy import ModelRole

SUPPORTED_LLM_PROVIDERS = frozenset({"moonshot", "anthropic", "bedrock"})


@dataclass(frozen=True, slots=True)
class ModelCatalogEntry:
    provider: str
    model_id: str
    display_name: str


# Platform defaults when env vars are unset — keep in sync with config.py defaults.
PLATFORM_MODEL_DEFAULTS: dict[ModelRole, ModelCatalogEntry] = {
    ModelRole.reviewer_standard: ModelCatalogEntry(
        provider="moonshot",
        model_id="kimi-k2.7-code",
        display_name="Kimi K2.7 Code",
    ),
    ModelRole.reviewer_deep: ModelCatalogEntry(
        provider="moonshot",
        model_id="kimi-k3",
        display_name="Kimi K3",
    ),
    ModelRole.reviewer_critical: ModelCatalogEntry(
        provider="moonshot",
        model_id="kimi-k3",
        display_name="Kimi K3",
    ),
    ModelRole.judge: ModelCatalogEntry(
        provider="anthropic",
        model_id="claude-sonnet-5",
        display_name="Claude Sonnet",
    ),
}

BEDROCK_CATALOG_EXAMPLES: tuple[ModelCatalogEntry, ...] = (
    ModelCatalogEntry(
        provider="bedrock",
        model_id="anthropic.claude-sonnet-4-20250514-v1:0",
        display_name="Claude Sonnet (Bedrock)",
    ),
    ModelCatalogEntry(
        provider="bedrock",
        model_id="anthropic.claude-3-5-sonnet-20241022-v2:0",
        display_name="Claude 3.5 Sonnet (Bedrock)",
    ),
)


def catalog_entries() -> list[ModelCatalogEntry]:
    """Deduped catalog list for future workspace policy API."""
    seen: set[tuple[str, str]] = set()
    entries: list[ModelCatalogEntry] = []
    for entry in PLATFORM_MODEL_DEFAULTS.values():
        key = (entry.provider, entry.model_id)
        if key in seen:
            continue
        seen.add(key)
        entries.append(entry)
    for entry in BEDROCK_CATALOG_EXAMPLES:
        key = (entry.provider, entry.model_id)
        if key in seen:
            continue
        seen.add(key)
        entries.append(entry)
    return entries
