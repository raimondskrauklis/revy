# backend/app/services/audit_service.py
"""Audit log writes and reads — AUDIT.md."""
from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import UTC, date, datetime, time
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

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
from app.schemas.admin import PlatformAuditListItem
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


def _audit_list_item(
    audit_row: AuditLogORM,
    actor: UserORM,
    impersonator: UserORM | None,
) -> AuditListItem:
    return AuditListItem(
        id=audit_row.id,
        created_at=audit_row.created_at,
        action=audit_row.action,
        resource_type=audit_row.resource_type,
        resource_id=audit_row.resource_id,
        actor_user_id=audit_row.actor_user_id,
        actor_email=actor.email,
        impersonator_user_id=audit_row.impersonator_user_id,
        impersonator_email=impersonator.email if impersonator else None,
        metadata=_cap_metadata(audit_row.metadata_json),
    )


async def list_workspace_audit(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    params: CursorParams,
) -> CursorResponse[AuditListItem]:
    impersonator_user = aliased(UserORM)
    stmt = (
        select(AuditLogORM, UserORM, impersonator_user)
        .join(UserORM, UserORM.id == AuditLogORM.actor_user_id)
        .outerjoin(
            impersonator_user,
            impersonator_user.id == AuditLogORM.impersonator_user_id,
        )
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

    items = [
        _audit_list_item(audit_row, actor, impersonator)
        for audit_row, actor, impersonator in rows
    ]

    next_cursor = None
    if has_next and rows:
        last_row, _, _ = rows[-1]
        next_cursor = encode_cursor(last_row.created_at, last_row.id)

    return CursorResponse(
        items=items,
        cursor=CursorMeta(next_cursor=next_cursor, has_next=has_next),
    )


@dataclass(frozen=True)
class PlatformAuditFilters:
    workspace_id: UUID | None = None
    actor_user_id: UUID | None = None
    action_prefix: str | None = None
    created_at_from: date | None = None
    created_at_to: date | None = None


async def list_platform_audit(
    session: AsyncSession,
    *,
    params: CursorParams,
    filters: PlatformAuditFilters | None = None,
) -> CursorResponse[PlatformAuditListItem]:
    active_filters = filters or PlatformAuditFilters()
    impersonator_user = aliased(UserORM)
    stmt = (
        select(AuditLogORM, UserORM, impersonator_user)
        .join(UserORM, UserORM.id == AuditLogORM.actor_user_id)
        .outerjoin(
            impersonator_user,
            impersonator_user.id == AuditLogORM.impersonator_user_id,
        )
    )

    if active_filters.workspace_id is not None:
        stmt = stmt.where(AuditLogORM.workspace_id == active_filters.workspace_id)
    if active_filters.actor_user_id is not None:
        stmt = stmt.where(AuditLogORM.actor_user_id == active_filters.actor_user_id)
    if active_filters.action_prefix:
        stmt = stmt.where(AuditLogORM.action.startswith(active_filters.action_prefix))
    if active_filters.created_at_from is not None:
        start = datetime.combine(active_filters.created_at_from, time.min, tzinfo=UTC)
        stmt = stmt.where(AuditLogORM.created_at >= start)
    if active_filters.created_at_to is not None:
        end = datetime.combine(active_filters.created_at_to, time.max, tzinfo=UTC)
        stmt = stmt.where(AuditLogORM.created_at <= end)

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

    items: list[PlatformAuditListItem] = []
    for audit_row, actor, impersonator in rows:
        base = _audit_list_item(audit_row, actor, impersonator)
        items.append(
            PlatformAuditListItem(
                **base.model_dump(),
                workspace_id=audit_row.workspace_id,
            )
        )

    next_cursor = None
    if has_next and rows:
        last_row, _, _ = rows[-1]
        next_cursor = encode_cursor(last_row.created_at, last_row.id)

    return CursorResponse(
        items=items,
        cursor=CursorMeta(next_cursor=next_cursor, has_next=has_next),
    )
