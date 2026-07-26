# backend/app/api/v1/workspaces/model_policy.py
"""Workspace model policy routes — MODEL_POLICY M2."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.auth import CurrentUser, get_current_user
from app.core.database import get_db
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.permissions import Permission, require_permission
from app.core.tenancy import require_same_workspace
from app.models.workspaces import WorkspaceORM
from app.schemas.common import SuccessResponse
from app.schemas.model_policy import (
    ModelCatalogItem,
    ModelCatalogResponse,
    ModelPolicyPatch,
    ModelPolicyResponse,
)
from app.services.model_catalog import build_model_catalog, catalog_region_for_provider
from app.services.workspace_model_policy import (
    get_workspace_model_policy,
    patch_workspace_model_policy,
)

router = APIRouter(tags=["workspaces"])


@router.get("/{workspace_id}/model-policy", response_model=SuccessResponse[ModelPolicyResponse])
async def get_model_policy(
    workspace_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[ModelPolicyResponse]:
    require_permission(current_user, Permission.admin_users)
    require_same_workspace(current_user, workspace_id)

    workspace = await session.get(WorkspaceORM, workspace_id)
    if workspace is None:
        raise NotFoundError("Workspace not found")

    data = await get_workspace_model_policy(session, workspace_id=workspace_id)
    return SuccessResponse(data=data)


@router.patch("/{workspace_id}/model-policy", response_model=SuccessResponse[ModelPolicyResponse])
async def patch_model_policy(
    workspace_id: UUID,
    body: ModelPolicyPatch,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[ModelPolicyResponse]:
    require_permission(current_user, Permission.admin_users)
    require_same_workspace(current_user, workspace_id)
    if current_user.user_id is None:
        raise ForbiddenError(message="User not provisioned")

    workspace = await session.get(WorkspaceORM, workspace_id)
    if workspace is None:
        raise NotFoundError("Workspace not found")

    data = await patch_workspace_model_policy(
        session,
        workspace_id=workspace_id,
        body=body,
        actor_user_id=current_user.user_id,
        impersonator_user_id=current_user.impersonator_user_id,
    )
    await session.commit()
    return SuccessResponse(data=data)


@router.get("/{workspace_id}/model-catalog", response_model=SuccessResponse[ModelCatalogResponse])
async def get_model_catalog(
    workspace_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[ModelCatalogResponse]:
    _ = session
    require_permission(current_user, Permission.admin_users)
    require_same_workspace(current_user, workspace_id)

    workspace = await session.get(WorkspaceORM, workspace_id)
    if workspace is None:
        raise NotFoundError("Workspace not found")

    catalog = build_model_catalog()
    roles = {
        role: [
            ModelCatalogItem(
                provider=entry.provider,
                model_id=entry.model_id,
                display_name=entry.display_name,
                region=catalog_region_for_provider(entry.provider),
            )
            for entry in entries
        ]
        for role, entries in catalog.items()
    }
    return SuccessResponse(data=ModelCatalogResponse(roles=roles))
