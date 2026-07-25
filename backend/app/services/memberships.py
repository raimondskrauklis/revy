# backend/app/services/memberships.py
"""Workspace membership management — TENANCY.md."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import AppRole
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.core.pagination import (
    CursorMeta,
    CursorParams,
    CursorResponse,
    InvalidCursorError,
    decode_cursor,
    encode_cursor,
)
from app.models.users import UserORM
from app.models.workspace_memberships import WorkspaceMembershipORM
from app.models.workspaces import WorkspaceORM
from app.schemas.memberships import MemberListItem
from app.services.audit_service import record_audit


async def _count_workspace_admins(session: AsyncSession, *, workspace_id: UUID) -> int:
    count = await session.scalar(
        select(func.count())
        .select_from(WorkspaceMembershipORM)
        .where(
            WorkspaceMembershipORM.workspace_id == workspace_id,
            WorkspaceMembershipORM.role == AppRole.admin,
        )
    )
    return int(count or 0)


async def _assert_not_last_admin(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    membership: WorkspaceMembershipORM,
) -> None:
    if membership.role != AppRole.admin:
        return

    workspace = await session.scalar(
        select(WorkspaceORM).where(WorkspaceORM.id == workspace_id).with_for_update()
    )
    if workspace is None:
        raise NotFoundError("Workspace not found")

    admin_count = await _count_workspace_admins(session, workspace_id=workspace_id)
    if admin_count <= 1:
        raise ForbiddenError(
            message="Cannot remove or demote the last workspace admin",
            error_code="last_workspace_admin",
        )


async def list_members(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    params: CursorParams,
) -> CursorResponse[MemberListItem]:
    stmt = (
        select(WorkspaceMembershipORM, UserORM)
        .join(UserORM, UserORM.id == WorkspaceMembershipORM.user_id)
        .where(WorkspaceMembershipORM.workspace_id == workspace_id)
    )

    if params.cursor:
        try:
            cursor_ts, cursor_id = decode_cursor(params.cursor)
        except InvalidCursorError as exc:
            raise ValidationError(message="Invalid cursor", field="cursor") from exc
        stmt = stmt.where(
            (WorkspaceMembershipORM.created_at < cursor_ts)
            | (
                (WorkspaceMembershipORM.created_at == cursor_ts)
                & (WorkspaceMembershipORM.user_id < cursor_id)
            )
        )

    stmt = stmt.order_by(
        WorkspaceMembershipORM.created_at.desc(),
        WorkspaceMembershipORM.user_id.desc(),
    ).limit(params.limit + 1)
    result = await session.execute(stmt)
    rows = list(result.all())

    has_next = len(rows) > params.limit
    if has_next:
        rows = rows[: params.limit]

    items: list[MemberListItem] = []
    for membership, user in rows:
        items.append(
            MemberListItem(
                user_id=membership.user_id,
                email=user.email,
                full_name=user.full_name,
                role=membership.role,
                created_at=membership.created_at,
            )
        )

    next_cursor = None
    if has_next and rows:
        last_membership, _ = rows[-1]
        next_cursor = encode_cursor(last_membership.created_at, last_membership.user_id)

    return CursorResponse(
        items=items,
        cursor=CursorMeta(next_cursor=next_cursor, has_next=has_next),
    )


async def count_members(session: AsyncSession, *, workspace_id: UUID) -> int:
    total = await session.scalar(
        select(func.count())
        .select_from(WorkspaceMembershipORM)
        .where(WorkspaceMembershipORM.workspace_id == workspace_id)
    )
    return int(total or 0)


async def _get_membership(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    user_id: UUID,
) -> WorkspaceMembershipORM:
    membership = await session.scalar(
        select(WorkspaceMembershipORM)
        .where(
            WorkspaceMembershipORM.workspace_id == workspace_id,
            WorkspaceMembershipORM.user_id == user_id,
        )
        .with_for_update()
    )
    if membership is None:
        raise NotFoundError("Member not found")
    return membership


async def update_member_role(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    user_id: UUID,
    role: AppRole,
    actor_user_id: UUID | None = None,
    impersonator_user_id: UUID | None = None,
) -> WorkspaceMembershipORM:
    membership = await _get_membership(session, workspace_id=workspace_id, user_id=user_id)
    old_role = membership.role
    if membership.role == AppRole.admin and role != AppRole.admin:
        await _assert_not_last_admin(session, workspace_id=workspace_id, membership=membership)
    membership.role = role
    await session.flush()

    if actor_user_id is not None and old_role != role:
        await record_audit(
            session,
            actor_user_id=actor_user_id,
            impersonator_user_id=impersonator_user_id,
            workspace_id=workspace_id,
            action="workspace_member.role_changed",
            resource_type="workspace_member",
            resource_id=str(user_id),
            metadata={
                "user_id": str(user_id),
                "old_role": old_role.value,
                "new_role": role.value,
            },
        )

    return membership


async def remove_member(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    user_id: UUID,
    actor_user_id: UUID | None = None,
    impersonator_user_id: UUID | None = None,
) -> None:
    membership = await _get_membership(session, workspace_id=workspace_id, user_id=user_id)
    removed_role = membership.role
    await _assert_not_last_admin(session, workspace_id=workspace_id, membership=membership)
    await session.delete(membership)
    await session.flush()

    if actor_user_id is not None:
        await record_audit(
            session,
            actor_user_id=actor_user_id,
            impersonator_user_id=impersonator_user_id,
            workspace_id=workspace_id,
            action="workspace_member.removed",
            resource_type="workspace_member",
            resource_id=str(user_id),
            metadata={"user_id": str(user_id), "role": removed_role.value},
        )
