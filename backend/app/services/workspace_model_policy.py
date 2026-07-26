# backend/app/services/workspace_model_policy.py
"""Workspace model policy CRUD — MODEL_POLICY M2."""

from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.model_policy import ModelRole
from app.core.exceptions import ValidationError
from app.models.workspace_model_policy import WorkspaceModelPolicyORM
from app.schemas.model_policy import ModelPolicyEntry, ModelPolicyPatch, ModelPolicyResponse
from app.services.audit_service import record_audit
from app.services.model_catalog import catalog_region_for_provider, is_valid_catalog_entry
from app.services.model_policy import ModelRef, resolve_model

_POLICY_ROLES = (
    ModelRole.reviewer_standard,
    ModelRole.reviewer_deep,
    ModelRole.reviewer_critical,
    ModelRole.judge,
)

_ROLE_FIELD_MAP: dict[str, ModelRole] = {
    "reviewer_standard": ModelRole.reviewer_standard,
    "reviewer_deep": ModelRole.reviewer_deep,
    "reviewer_critical": ModelRole.reviewer_critical,
    "judge": ModelRole.judge,
}


def _entry_from_row(row: WorkspaceModelPolicyORM) -> ModelPolicyEntry:
    return ModelPolicyEntry(
        provider=row.provider,
        model_id=row.model_id,
        region=row.region,
    )


def _ref_to_entry(model_ref: ModelRef) -> ModelPolicyEntry:
    return ModelPolicyEntry(
        provider=model_ref.provider,
        model_id=model_ref.model_id,
        region=model_ref.region,
    )


def _bedrock_region_for_patch(*, field: str, client_region: str | None) -> str:
    """Bedrock region is platform-scoped — workspace admins cannot redirect inference."""
    platform_region = catalog_region_for_provider("bedrock")
    if not platform_region:
        raise ValidationError(
            message="AWS region is not configured for Bedrock",
            field=field,
        )
    if client_region is not None and client_region.strip() != platform_region:
        raise ValidationError(
            message="Bedrock region must match platform AWS region",
            field=field,
        )
    return platform_region


async def get_workspace_model_policy(
    session: AsyncSession,
    *,
    workspace_id: UUID,
) -> ModelPolicyResponse:
    rows = (
        await session.scalars(
            select(WorkspaceModelPolicyORM).where(
                WorkspaceModelPolicyORM.workspace_id == workspace_id,
            )
        )
    ).all()
    by_role = {row.role: row for row in rows}

    overrides: dict[str, ModelPolicyEntry | None] = {}
    effective: dict[str, ModelPolicyEntry] = {}
    for field, role in _ROLE_FIELD_MAP.items():
        row = by_role.get(role.value)
        overrides[field] = _entry_from_row(row) if row is not None else None
        model_ref = await resolve_model(
            session,
            workspace_id,
            role,
            require_credentials=False,
        )
        effective[field] = _ref_to_entry(model_ref)

    return ModelPolicyResponse(overrides=overrides, effective=effective)


async def patch_workspace_model_policy(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    body: ModelPolicyPatch,
    actor_user_id: UUID,
    impersonator_user_id: UUID | None = None,
) -> ModelPolicyResponse:
    updates = body.model_dump(exclude_unset=True)
    if not updates:
        return await get_workspace_model_policy(session, workspace_id=workspace_id)

    changed_roles: list[str] = []
    for field in updates:
        value = getattr(body, field)
        role = _ROLE_FIELD_MAP[field]
        if value is None:
            result = await session.execute(
                delete(WorkspaceModelPolicyORM).where(
                    WorkspaceModelPolicyORM.workspace_id == workspace_id,
                    WorkspaceModelPolicyORM.role == role.value,
                )
            )
            if result.rowcount:
                changed_roles.append(role.value)
            continue

        provider = value.provider.strip().lower()
        model_id = value.model_id.strip()
        if not is_valid_catalog_entry(role=role, provider=provider, model_id=model_id):
            raise ValidationError(
                message="Model is not available for this role",
                field=field,
            )

        if provider == "bedrock":
            region = _bedrock_region_for_patch(field=field, client_region=value.region)
        elif value.region is not None:
            raise ValidationError(
                message="Region is only valid for Bedrock models",
                field=field,
            )
        else:
            region = None

        existing = await session.scalar(
            select(WorkspaceModelPolicyORM).where(
                WorkspaceModelPolicyORM.workspace_id == workspace_id,
                WorkspaceModelPolicyORM.role == role.value,
            )
        )
        if existing is None:
            session.add(
                WorkspaceModelPolicyORM(
                    workspace_id=workspace_id,
                    role=role.value,
                    provider=provider,
                    model_id=model_id,
                    region=region,
                )
            )
            changed_roles.append(role.value)
        else:
            changed = (
                existing.provider != provider
                or existing.model_id != model_id
                or existing.region != region
            )
            existing.provider = provider
            existing.model_id = model_id
            existing.region = region
            if changed:
                changed_roles.append(role.value)
        await session.flush()

    if changed_roles:
        await record_audit(
            session,
            actor_user_id=actor_user_id,
            impersonator_user_id=impersonator_user_id,
            workspace_id=workspace_id,
            action="workspace.model_policy_updated",
            resource_type="workspace",
            resource_id=str(workspace_id),
            metadata={"roles": changed_roles},
        )

    return await get_workspace_model_policy(session, workspace_id=workspace_id)
