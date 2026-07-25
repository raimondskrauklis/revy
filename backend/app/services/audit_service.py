# backend/app/services/audit_service.py
"""Audit log writes and reads — AUDIT.md."""
from __future__ import annotations

import json
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ValidationError
from app.core.pagination import (
    CursorMeta,
    CursorParams,
    CursorResponse,
    InvalidCursorError,
    decode_cursor,
    encode_cursor,
)
from app.models.audit_log import AuditLogORM
from app.models.users import UserORM
from app.schemas.audit import AuditListItem

_METADATA_MAX_BYTES = 4096


def _cap_metadata(metadata: dict[str, Any]) -> dict[str, Any]:
    try:
        serialized = json.dumps(metadata, separators=(",", ":"), default=str)
    except (TypeError, ValueError):
        return {}
    if len(serialized.encode("utf-8")) > _METADATA_MAX_BYTES:
        return {}
    return metadata


async def record_audit(
    session: AsyncSession,
    *,
    actor_user_id: UUID,
    workspace_id: UUID | None,
    action: str,
    resource_type: str | None = None,
    resource_id: str | None = None,
    metadata: dict[str, Any] | None = None,
    impersonator_user_id: UUID | None = None,
) -> AuditLogORM:
    row = AuditLogORM(
        actor_user_id=actor_user_id,
        impersonator_user_id=impersonator_user_id,
        workspace_id=workspace_id,
        action=action,
        resource_type=resource_type,
        resource_id=resource_id,
        metadata_json=metadata or {},
    )
    session.add(row)
    await session.flush()
    return row


async def list_workspace_audit(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    params: CursorParams,
) -> CursorResponse[AuditListItem]:
    stmt = (
        select(AuditLogORM, UserORM)
        .join(UserORM, UserORM.id == AuditLogORM.actor_user_id)
        .where(AuditLogORM.workspace_id == workspace_id)
    )

    if params.cursor:
        try:
            cursor_ts, cursor_id = decode_cursor(params.cursor)
        except InvalidCursorError as exc:
            raise ValidationError(message="Invalid cursor", field="cursor") from exc
        stmt = stmt.where(
            (AuditLogORM.created_at < cursor_ts)
            | ((AuditLogORM.created_at == cursor_ts) & (AuditLogORM.id < cursor_id))
        )

    stmt = stmt.order_by(AuditLogORM.created_at.desc(), AuditLogORM.id.desc()).limit(
        params.limit + 1
    )
    result = await session.execute(stmt)
    rows = list(result.all())

    has_next = len(rows) > params.limit
    if has_next:
        rows = rows[: params.limit]

    items: list[AuditListItem] = []
    for audit_row, actor in rows:
        items.append(
            AuditListItem(
                id=audit_row.id,
                created_at=audit_row.created_at,
                action=audit_row.action,
                resource_type=audit_row.resource_type,
                resource_id=audit_row.resource_id,
                actor_user_id=audit_row.actor_user_id,
                actor_email=actor.email,
                metadata=_cap_metadata(audit_row.metadata_json),
            )
        )

    next_cursor = None
    if has_next and rows:
        last_row, _ = rows[-1]
        next_cursor = encode_cursor(last_row.created_at, last_row.id)

    return CursorResponse(
        items=items,
        cursor=CursorMeta(next_cursor=next_cursor, has_next=has_next),
    )
