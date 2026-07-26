# backend/app/services/model_policy.py
"""Platform model resolver — MODEL_POLICY M0/M2."""

from __future__ import annotations

from dataclasses import dataclass
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.model_policy import ModelRole
from app.constants.model_registry import BEDROCK_CATALOG_EXAMPLES, PLATFORM_MODEL_DEFAULTS
from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError, ValidationError
from app.models.workspace_model_policy import WorkspaceModelPolicyORM
from app.services.model_catalog import is_valid_catalog_entry

_REVIEWER_ROLES = frozenset(
    {
        ModelRole.reviewer_standard,
        ModelRole.reviewer_deep,
        ModelRole.reviewer_critical,
    }
)


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


def _provider_credentials_configured(
    provider: str,
    *,
    role: ModelRole,
    model_id: str | None = None,
) -> bool:
    normalized = provider.strip().lower()
    if normalized == "moonshot":
        return bool(settings.moonshot_api_key and settings.moonshot_api_key.strip())
    if normalized == "anthropic":
        return bool(settings.anthropic_api_key and settings.anthropic_api_key.strip())
    if normalized == "bedrock":
        if not (settings.aws_region or "").strip():
            return False
        if model_id and model_id.strip():
            return True
        if role in _REVIEWER_ROLES:
            return bool((settings.revy_bedrock_reviewer_model_id or "").strip())
        if role == ModelRole.judge:
            return bool((settings.revy_bedrock_judge_model_id or "").strip())
        return False
    return False


def _assert_provider_credentials(
    provider: str,
    *,
    role: ModelRole,
    model_id: str | None = None,
) -> None:
    if _provider_credentials_configured(provider, role=role, model_id=model_id):
        return
    if role in _REVIEWER_ROLES:
        raise ServiceUnavailableError(
            message="Reviewer LLM API is not configured",
            error_code="llm_disabled",
        )
    if role == ModelRole.judge:
        raise ServiceUnavailableError(
            message="Judge LLM API is not configured",
            error_code="llm_disabled",
        )
    raise ValueError(f"Unsupported model role: {role}")


def _resolve_platform_model(role: ModelRole, *, require_credentials: bool = True) -> ModelRef:
    if role in _REVIEWER_ROLES:
        provider = settings.effective_reviewer_provider
        if require_credentials:
            _assert_provider_credentials(provider, role=role)
        model_id = _resolve_reviewer_model_id(provider, role)
        region = settings.aws_region if provider == "bedrock" else None
        return ModelRef(provider=provider, model_id=model_id, region=region)

    if role == ModelRole.judge:
        provider = settings.effective_judge_provider
        if require_credentials:
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


async def _resolve_workspace_override(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    role: ModelRole,
    require_credentials: bool = True,
) -> ModelRef | None:
    row = await session.scalar(
        select(WorkspaceModelPolicyORM).where(
            WorkspaceModelPolicyORM.workspace_id == workspace_id,
            WorkspaceModelPolicyORM.role == role.value,
        )
    )
    if row is None:
        return None

    provider = row.provider.strip().lower()
    model_id = row.model_id.strip()
    if require_credentials and not is_valid_catalog_entry(
        role=role,
        provider=provider,
        model_id=model_id,
    ):
        raise ValidationError(
            message="Workspace model override is no longer valid",
            field=role.value,
        )

    region = None
    if provider == "bedrock":
        region = (settings.aws_region or "").strip() or None
    if require_credentials:
        _assert_provider_credentials(provider, role=role, model_id=model_id)
    return ModelRef(provider=provider, model_id=model_id, region=region)


async def resolve_model(
    session: AsyncSession,
    workspace_id: UUID,
    role: ModelRole,
    *,
    require_credentials: bool = True,
) -> ModelRef:
    """Resolve provider + model for a pipeline role."""
    override = await _resolve_workspace_override(
        session,
        workspace_id=workspace_id,
        role=role,
        require_credentials=require_credentials,
    )
    if override is not None:
        return override
    return _resolve_platform_model(role, require_credentials=require_credentials)
