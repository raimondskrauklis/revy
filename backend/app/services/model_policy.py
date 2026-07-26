# backend/app/services/model_policy.py
"""Platform model resolver — MODEL_POLICY M0 (env-only; workspace overrides in M2)."""
from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.model_policy import ModelRole
from app.constants.model_registry import BEDROCK_CATALOG_EXAMPLES, PLATFORM_MODEL_DEFAULTS
from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError

_REVIEWER_ROLES = frozenset({
    ModelRole.reviewer_standard,
    ModelRole.reviewer_deep,
    ModelRole.reviewer_critical,
})


@dataclass(frozen=True, slots=True)
class ModelRef:
    provider: str
    model_id: str
    region: str | None = None


def review_profile_to_model_role(profile: str) -> ModelRole:
    normalized = (profile or settings.revy_default_review_profile).strip().lower()
    if normalized == "deep":
        return ModelRole.reviewer_deep
    if normalized == "critical":
        return ModelRole.reviewer_critical
    return ModelRole.reviewer_standard


def _reviewer_model_id_for_role(role: ModelRole) -> str:
    if role == ModelRole.reviewer_deep:
        return settings.revy_moonshot_model_deep
    if role == ModelRole.reviewer_critical:
        return settings.revy_moonshot_model_critical
    return settings.revy_moonshot_model_standard


def _resolve_reviewer_model_id(provider: str, role: ModelRole) -> str:
    if provider == "moonshot":
        return _reviewer_model_id_for_role(role)
    if provider == "anthropic":
        return settings.revy_anthropic_model
    if provider == "bedrock":
        model_id = (settings.revy_bedrock_reviewer_model_id or "").strip()
        if not model_id:
            model_id = BEDROCK_CATALOG_EXAMPLES[0].model_id
        return model_id
    return PLATFORM_MODEL_DEFAULTS[role].model_id


def _assert_provider_credentials(provider: str, *, role: ModelRole) -> None:
    if role in _REVIEWER_ROLES:
        if not settings.reviewer_llm_enabled():
            raise ServiceUnavailableError(
                message="Reviewer LLM API is not configured",
                error_code="llm_disabled",
            )
        return
    if role == ModelRole.judge:
        if not settings.judge_llm_enabled():
            raise ServiceUnavailableError(
                message="Judge LLM API is not configured",
                error_code="llm_disabled",
            )
        return
    if provider == "moonshot" and not settings.moonshot_api_key:
        raise ServiceUnavailableError(
            message="Moonshot API is not configured",
            error_code="llm_disabled",
        )
    if provider == "anthropic" and not settings.anthropic_api_key:
        raise ServiceUnavailableError(
            message="Anthropic API is not configured",
            error_code="llm_disabled",
        )


async def resolve_model(
    session: AsyncSession,
    workspace_id: UUID,
    role: ModelRole,
) -> ModelRef:
    """Resolve provider + model for a pipeline role (M0: platform env only)."""
    _ = session, workspace_id  # workspace overrides — M2

    if role in _REVIEWER_ROLES:
        provider = settings.effective_reviewer_provider
        _assert_provider_credentials(provider, role=role)
        model_id = _resolve_reviewer_model_id(provider, role)
        region = settings.aws_region if provider == "bedrock" else None
        return ModelRef(provider=provider, model_id=model_id, region=region)

    if role == ModelRole.judge:
        provider = settings.effective_judge_provider
        _assert_provider_credentials(provider, role=role)
        if provider == "anthropic":
            model_id = settings.revy_anthropic_model
            region = None
        elif provider == "bedrock":
            model_id = (settings.revy_bedrock_judge_model_id or "").strip()
            if not model_id:
                model_id = BEDROCK_CATALOG_EXAMPLES[0].model_id
            region = settings.aws_region
        else:
            model_id = PLATFORM_MODEL_DEFAULTS[ModelRole.judge].model_id
            region = None
        return ModelRef(provider=provider, model_id=model_id, region=region)

    raise ValueError(f"Unsupported model role: {role}")
