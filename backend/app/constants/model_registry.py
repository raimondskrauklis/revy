# backend/app/constants/model_registry.py
"""Known (provider, model_id) catalog — platform defaults and M2 API catalog."""
from __future__ import annotations

from dataclasses import dataclass

from app.constants.model_policy import ModelRole

SUPPORTED_LLM_PROVIDERS = frozenset({"moonshot", "rtu", "anthropic", "bedrock"})
SUPPORTED_JUDGE_PROVIDERS = frozenset({"rtu", "anthropic", "bedrock"})


def normalize_provider_slug(provider: str) -> str:
    """Normalize provider identifiers from API input or env."""
    return provider.strip().lower()


@dataclass(frozen=True, slots=True)
class ModelCatalogEntry:
    provider: str
    model_id: str
    display_name: str


MOONSHOT_REVIEWER_CATALOG: tuple[ModelCatalogEntry, ...] = (
    ModelCatalogEntry(
        provider="moonshot",
        model_id="kimi-k2.7-code",
        display_name="Kimi K2.7 Code",
    ),
    ModelCatalogEntry(
        provider="moonshot",
        model_id="kimi-k3",
        display_name="Kimi K3",
    ),
)

# Platform defaults when env vars are unset — keep in sync with config.py defaults.
PLATFORM_MODEL_DEFAULTS: dict[ModelRole, ModelCatalogEntry] = {
    ModelRole.reviewer_standard: ModelCatalogEntry(
        provider="rtu",
        model_id="azure_ai/kimi-k2.7-code",
        display_name="Kimi K2.7 Code (RTU)",
    ),
    ModelRole.reviewer_deep: ModelCatalogEntry(
        provider="rtu",
        model_id="azure_ai/claude-fable-5-1",
        display_name="Claude Fable 5.1 (RTU)",
    ),
    ModelRole.reviewer_critical: ModelCatalogEntry(
        provider="rtu",
        model_id="azure_ai/claude-fable-5-1",
        display_name="Claude Fable 5.1 (RTU)",
    ),
    ModelRole.judge: ModelCatalogEntry(
        provider="rtu",
        model_id="azure_ai/claude-opus-5",
        display_name="Claude Opus 5 (RTU)",
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
    for entry in (*PLATFORM_MODEL_DEFAULTS.values(), *MOONSHOT_REVIEWER_CATALOG, *BEDROCK_CATALOG_EXAMPLES):
        key = (entry.provider, entry.model_id)
        if key in seen:
            continue
        seen.add(key)
        entries.append(entry)
    return entries
