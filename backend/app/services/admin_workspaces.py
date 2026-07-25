# backend/app/services/admin_workspaces.py
"""Platform admin workspace directory — W5."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import WorkspaceStatus
from app.core.exceptions import NotFoundError, ValidationError
from app.core.pagination import (
    CursorMeta,
    CursorParams,
    CursorResponse,
    InvalidCursorError,
    decode_cursor,
    encode_cursor,
)
from app.models.workspace_memberships import WorkspaceMembershipORM
from app.models.workspaces import WorkspaceORM
from app.schemas.admin import AdminWorkspaceDetail, AdminWorkspaceListItem
from app.services.audit_service import record_audit


def _mask_stripe_customer_id(customer_id: str | None) -> str | None:
    if not customer_id:
        return None
    return "cus_***"


def _member_count_subquery():
    return (
        select(
            WorkspaceMembershipORM.workspace_id.label("workspace_id"),
            func.count().label("member_count"),
        )
        .group_by(WorkspaceMembershipORM.workspace_id)
        .subquery()
    )


async def _get_member_count(
    session: AsyncSession,
    *,
    workspace_id: UUID,
) -> int:
    count = await session.scalar(
        select(func.count())
        .select_from(WorkspaceMembershipORM)
        .where(WorkspaceMembershipORM.workspace_id == workspace_id)
    )
    return int(count or 0)


async def list_workspaces(
    session: AsyncSession,
    *,
    params: CursorParams,
    status: WorkspaceStatus | None = None,
    search: str | None = None,
) -> CursorResponse[AdminWorkspaceListItem]:
    member_counts = _member_count_subquery()
    stmt = (
        select(
            WorkspaceORM,
            func.coalesce(member_counts.c.member_count, 0).label("member_count"),
        )
        .outerjoin(member_counts, member_counts.c.workspace_id == WorkspaceORM.id)
    )

    if status is not None:
        stmt = stmt.where(WorkspaceORM.status == status)

    trimmed_search = (search or "").strip()
    if trimmed_search:
        pattern = f"%{trimmed_search}%"
        stmt = stmt.where(
            or_(
                WorkspaceORM.name.ilike(pattern),
                WorkspaceORM.slug.ilike(pattern),
            )
        )

    if params.cursor:
        try:
            cursor_ts, cursor_id = decode_cursor(params.cursor)
        except InvalidCursorError as exc:
            raise ValidationError(message="Invalid cursor", field="cursor") from exc
        stmt = stmt.where(
            (WorkspaceORM.created_at < cursor_ts)
            | ((WorkspaceORM.created_at == cursor_ts) & (WorkspaceORM.id < cursor_id))
        )

    stmt = stmt.order_by(WorkspaceORM.created_at.desc(), WorkspaceORM.id.desc()).limit(
        params.limit + 1
    )
    result = await session.execute(stmt)
    rows = list(result.all())

    has_next = len(rows) > params.limit
    if has_next:
        rows = rows[: params.limit]

    items: list[AdminWorkspaceListItem] = []
    for workspace, member_count in rows:
        items.append(
            AdminWorkspaceListItem(
                id=workspace.id,
                name=workspace.name,
                slug=workspace.slug,
                status=workspace.status,
                plan=workspace.plan,
                member_count=int(member_count),
                created_at=workspace.created_at,
            )
        )

    next_cursor = None
    if has_next and rows:
        last_workspace, _ = rows[-1]
        next_cursor = encode_cursor(last_workspace.created_at, last_workspace.id)

    return CursorResponse(
        items=items,
        cursor=CursorMeta(next_cursor=next_cursor, has_next=has_next),
    )


async def get_workspace_detail(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    actor_user_id: UUID,
) -> AdminWorkspaceDetail:
    workspace = await session.get(WorkspaceORM, workspace_id)
    if workspace is None:
        raise NotFoundError("Workspace not found")

    member_count = await _get_member_count(session, workspace_id=workspace_id)

    await record_audit(
        session,
        actor_user_id=actor_user_id,
        workspace_id=workspace_id,
        action="platform.workspace.viewed",
        resource_type="workspace",
        resource_id=str(workspace_id),
    )

    return AdminWorkspaceDetail(
        id=workspace.id,
        name=workspace.name,
        slug=workspace.slug,
        status=workspace.status,
        plan=workspace.plan,
        member_count=member_count,
        stripe_customer_id=_mask_stripe_customer_id(workspace.stripe_customer_id),
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )


async def suspend_workspace(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    actor_user_id: UUID,
) -> AdminWorkspaceDetail:
    workspace = await session.get(WorkspaceORM, workspace_id)
    if workspace is None:
        raise NotFoundError("Workspace not found")

    workspace.status = WorkspaceStatus.suspended
    await session.flush()

    await record_audit(
        session,
        actor_user_id=actor_user_id,
        workspace_id=workspace_id,
        action="platform.workspace.suspended",
        resource_type="workspace",
        resource_id=str(workspace_id),
    )

    member_count = await _get_member_count(session, workspace_id=workspace_id)
    return AdminWorkspaceDetail(
        id=workspace.id,
        name=workspace.name,
        slug=workspace.slug,
        status=workspace.status,
        plan=workspace.plan,
        member_count=member_count,
        stripe_customer_id=_mask_stripe_customer_id(workspace.stripe_customer_id),
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )


async def unsuspend_workspace(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    actor_user_id: UUID,
) -> AdminWorkspaceDetail:
    workspace = await session.get(WorkspaceORM, workspace_id)
    if workspace is None:
        raise NotFoundError("Workspace not found")

    workspace.status = WorkspaceStatus.active
    await session.flush()

    await record_audit(
        session,
        actor_user_id=actor_user_id,
        workspace_id=workspace_id,
        action="platform.workspace.unsuspended",
        resource_type="workspace",
        resource_id=str(workspace_id),
    )

    member_count = await _get_member_count(session, workspace_id=workspace_id)
    return AdminWorkspaceDetail(
        id=workspace.id,
        name=workspace.name,
        slug=workspace.slug,
        status=workspace.status,
        plan=workspace.plan,
        member_count=member_count,
        stripe_customer_id=_mask_stripe_customer_id(workspace.stripe_customer_id),
        created_at=workspace.created_at,
        updated_at=workspace.updated_at,
    )
