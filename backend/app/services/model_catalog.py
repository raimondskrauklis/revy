# backend/app/services/model_catalog.py
"""Model catalog for workspace policy UI — MODEL_POLICY M2."""

from __future__ import annotations

from app.constants.model_policy import ModelRole
from app.constants.model_registry import (
    BEDROCK_CATALOG_EXAMPLES,
    PLATFORM_MODEL_DEFAULTS,
    ModelCatalogEntry,
)
from app.core.config import settings

_POLICY_ROLES = (
    ModelRole.reviewer_standard,
    ModelRole.reviewer_deep,
    ModelRole.reviewer_critical,
    ModelRole.judge,
)


def _moonshot_reviewer_entries() -> list[ModelCatalogEntry]:
    if not settings.moonshot_api_key or not settings.moonshot_api_key.strip():
        return []
    return [
        PLATFORM_MODEL_DEFAULTS[ModelRole.reviewer_standard],
        PLATFORM_MODEL_DEFAULTS[ModelRole.reviewer_deep],
        PLATFORM_MODEL_DEFAULTS[ModelRole.reviewer_critical],
    ]


def _anthropic_reviewer_entries() -> list[ModelCatalogEntry]:
    if not settings.anthropic_api_key or not settings.anthropic_api_key.strip():
        return []
    model_id = settings.revy_anthropic_model
    return [
        ModelCatalogEntry(
            provider="anthropic",
            model_id=model_id,
            display_name="Claude (Anthropic API)",
        ),
    ]


def _bedrock_reviewer_entries() -> list[ModelCatalogEntry]:
    if not settings.bedrock_enabled():
        return []
    model_id = (settings.revy_bedrock_reviewer_model_id or "").strip()
    if not model_id and BEDROCK_CATALOG_EXAMPLES:
        model_id = BEDROCK_CATALOG_EXAMPLES[0].model_id
    if not model_id:
        return []
    region = (settings.aws_region or "").strip() or None
    _ = region
    return [
        ModelCatalogEntry(
            provider="bedrock",
            model_id=model_id,
            display_name="Bedrock reviewer model",
        ),
        *BEDROCK_CATALOG_EXAMPLES,
    ]


def _anthropic_judge_entries() -> list[ModelCatalogEntry]:
    if settings.effective_judge_provider != "anthropic":
        return []
    if not settings.anthropic_api_key or not settings.anthropic_api_key.strip():
        return []
    return [PLATFORM_MODEL_DEFAULTS[ModelRole.judge]]


def _bedrock_judge_entries() -> list[ModelCatalogEntry]:
    if settings.effective_judge_provider != "bedrock":
        return []
    if not settings.bedrock_enabled():
        return []
    model_id = (settings.revy_bedrock_judge_model_id or "").strip()
    if not model_id and BEDROCK_CATALOG_EXAMPLES:
        model_id = BEDROCK_CATALOG_EXAMPLES[0].model_id
    if not model_id:
        return []
    return [
        ModelCatalogEntry(
            provider="bedrock",
            model_id=model_id,
            display_name="Bedrock judge model",
        ),
        *BEDROCK_CATALOG_EXAMPLES,
    ]


def _dedupe_entries(entries: list[ModelCatalogEntry]) -> list[ModelCatalogEntry]:
    seen: set[tuple[str, str]] = set()
    result: list[ModelCatalogEntry] = []
    for entry in entries:
        key = (entry.provider, entry.model_id)
        if key in seen:
            continue
        seen.add(key)
        result.append(entry)
    return result


def _entries_for_role(role: ModelRole) -> list[ModelCatalogEntry]:
    if role in (
        ModelRole.reviewer_standard,
        ModelRole.reviewer_deep,
        ModelRole.reviewer_critical,
    ):
        entries = [
            *_moonshot_reviewer_entries(),
            *_anthropic_reviewer_entries(),
            *_bedrock_reviewer_entries(),
        ]
        if role == ModelRole.reviewer_standard:
            return _dedupe_entries(entries)
        if role == ModelRole.reviewer_deep:
            deep = PLATFORM_MODEL_DEFAULTS[ModelRole.reviewer_deep]
            return _dedupe_entries([deep, *entries])
        critical = PLATFORM_MODEL_DEFAULTS[ModelRole.reviewer_critical]
        return _dedupe_entries([critical, *entries])

    if role == ModelRole.judge:
        return _dedupe_entries([*_anthropic_judge_entries(), *_bedrock_judge_entries()])

    return []


def build_model_catalog() -> dict[str, list[ModelCatalogEntry]]:
    return {role.value: _entries_for_role(role) for role in _POLICY_ROLES}


def is_valid_catalog_entry(*, role: ModelRole, provider: str, model_id: str) -> bool:
    normalized_provider = provider.strip().lower()
    normalized_model_id = model_id.strip()
    for entry in _entries_for_role(role):
        if entry.provider == normalized_provider and entry.model_id == normalized_model_id:
            return True
    return False


def catalog_region_for_provider(provider: str) -> str | None:
    if provider.strip().lower() == "bedrock":
        region = (settings.aws_region or "").strip()
        return region or None
    return None
