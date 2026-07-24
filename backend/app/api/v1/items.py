# backend/app/api/v1/items.py
"""Items — canonical CRUD + cursor list (AGENT_PATTERNS.md)."""
from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import JSONResponse

from app.core.auth import CurrentUser, get_current_user
from app.core.database import get_db
from app.core.exceptions import ForbiddenError
from app.core.idempotency import idempotency_guard
from app.core.pagination import CursorParams, CursorResponse, get_cursor_params
from app.core.permissions import Permission, require_permission
from app.core.tenancy import require_workspace, workspace_id_for_create
from app.schemas.common import SuccessResponse
from app.schemas.items import ItemCreate, ItemResponse, ItemUpdate
from app.services.items import (
    create_item,
    delete_item,
    get_item,
    list_items,
    update_item,
)

router = APIRouter(prefix="/items", tags=["items"])


@router.get("", response_model=SuccessResponse[CursorResponse[ItemResponse]])
async def get_items(
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    params: Annotated[CursorParams, Depends(get_cursor_params)],
) -> SuccessResponse[CursorResponse[ItemResponse]]:
    require_permission(current_user, Permission.items_view)
    workspace_id = require_workspace(current_user)
    page = await list_items(session, workspace_id=workspace_id, params=params)
    return SuccessResponse(data=page)


@router.post("", response_model=SuccessResponse[ItemResponse], status_code=status.HTTP_201_CREATED)
async def post_item(
    body: ItemCreate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
    idempotent: Annotated[JSONResponse | None, Depends(idempotency_guard)] = None,
) -> SuccessResponse[ItemResponse] | JSONResponse:
    if idempotent is not None:
        return idempotent
    require_permission(current_user, Permission.items_manage)
    if current_user.user_id is None:
        raise ForbiddenError(message="User not provisioned")
    workspace_id = workspace_id_for_create(current_user)
    item = await create_item(
        session,
        workspace_id=workspace_id,
        actor_user_id=current_user.user_id,
        payload=body,
    )
    await session.commit()
    return SuccessResponse(data=ItemResponse.model_validate(item))


@router.get("/{item_id}", response_model=SuccessResponse[ItemResponse])
async def get_item_by_id(
    item_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[ItemResponse]:
    require_permission(current_user, Permission.items_view)
    workspace_id = require_workspace(current_user)
    item = await get_item(session, workspace_id=workspace_id, item_id=item_id)
    return SuccessResponse(data=ItemResponse.model_validate(item))


@router.patch("/{item_id}", response_model=SuccessResponse[ItemResponse])
async def patch_item(
    item_id: UUID,
    body: ItemUpdate,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> SuccessResponse[ItemResponse]:
    require_permission(current_user, Permission.items_manage)
    if current_user.user_id is None:
        raise ForbiddenError(message="User not provisioned")
    workspace_id = require_workspace(current_user)
    item = await update_item(
        session,
        workspace_id=workspace_id,
        item_id=item_id,
        actor_user_id=current_user.user_id,
        payload=body,
    )
    await session.commit()
    return SuccessResponse(data=ItemResponse.model_validate(item))


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_item(
    item_id: UUID,
    current_user: Annotated[CurrentUser, Depends(get_current_user)],
    session: Annotated[AsyncSession, Depends(get_db)],
) -> None:
    require_permission(current_user, Permission.items_manage)
    if current_user.user_id is None:
        raise ForbiddenError(message="User not provisioned")
    workspace_id = require_workspace(current_user)
    await delete_item(
        session,
        workspace_id=workspace_id,
        item_id=item_id,
        actor_user_id=current_user.user_id,
    )
    await session.commit()
