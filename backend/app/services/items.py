# backend/app/services/items.py
"""Items CRUD + cursor list — reference service for AGENT_PATTERNS.md."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import ItemStatus
from app.core.exceptions import NotFoundError, ValidationError
from app.core.pagination import (
    CursorMeta,
    CursorParams,
    CursorResponse,
    InvalidCursorError,
    decode_cursor,
    encode_cursor,
)
from app.core.query_filters import active_only
from app.models.items import ItemORM
from app.schemas.items import ItemCreate, ItemResponse, ItemUpdate


async def list_items(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    params: CursorParams,
) -> CursorResponse[ItemResponse]:
    stmt = select(ItemORM).where(ItemORM.workspace_id == workspace_id)
    stmt = active_only(stmt, ItemORM)

    if params.cursor:
        try:
            cursor_ts, cursor_id = decode_cursor(params.cursor)
        except InvalidCursorError as exc:
            raise ValidationError(message="Invalid cursor", field="cursor") from exc
        stmt = stmt.where(
            (ItemORM.created_at < cursor_ts)
            | ((ItemORM.created_at == cursor_ts) & (ItemORM.id < cursor_id))
        )

    stmt = stmt.order_by(ItemORM.created_at.desc(), ItemORM.id.desc()).limit(params.limit + 1)
    result = await session.execute(stmt)
    rows = list(result.scalars().all())

    has_next = len(rows) > params.limit
    if has_next:
        rows = rows[: params.limit]

    next_cursor = None
    if has_next and rows:
        last = rows[-1]
        next_cursor = encode_cursor(last.created_at, last.id)

    return CursorResponse(
        items=[ItemResponse.model_validate(row) for row in rows],
        cursor=CursorMeta(next_cursor=next_cursor, has_next=has_next),
    )


async def get_item(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    item_id: UUID,
) -> ItemORM:
    stmt = active_only(
        select(ItemORM).where(
            ItemORM.id == item_id,
            ItemORM.workspace_id == workspace_id,
        ),
        ItemORM,
    )
    row = await session.scalar(stmt)
    if row is None:
        raise NotFoundError("Item not found")
    return row


async def create_item(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    actor_user_id: UUID,
    payload: ItemCreate,
) -> ItemORM:
    item = ItemORM(
        workspace_id=workspace_id,
        name=payload.name.strip(),
        status=payload.status.value,
        created_by_id=actor_user_id,
        updated_by_id=actor_user_id,
    )
    session.add(item)
    await session.flush()
    return item


async def update_item(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    item_id: UUID,
    actor_user_id: UUID,
    payload: ItemUpdate,
) -> ItemORM:
    item = await get_item(session, workspace_id=workspace_id, item_id=item_id)

    if payload.name is not None:
        item.name = payload.name.strip()
    if payload.status is not None:
        item.status = payload.status.value
    item.updated_by_id = actor_user_id
    await session.flush()
    return item


async def delete_item(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    item_id: UUID,
    actor_user_id: UUID,
) -> None:
    item = await get_item(session, workspace_id=workspace_id, item_id=item_id)
    item.soft_delete(deleted_by_id=actor_user_id)
    await session.flush()


def default_item_status() -> ItemStatus:
    """Regression anchor for unit tests."""
    return ItemStatus.draft
