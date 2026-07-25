# backend/app/services/impersonation.py
"""Super-admin impersonation sessions — W7."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import PlatformRole, UserStatus
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.core.pagination import (
    CursorMeta,
    CursorParams,
    CursorResponse,
    InvalidCursorError,
    decode_cursor,
    encode_cursor,
)
from app.models.impersonation_session import ImpersonationSessionORM
from app.models.users import UserORM
from app.models.workspace_memberships import WorkspaceMembershipORM
from app.models.workspaces import WorkspaceORM
from app.schemas.impersonation import ActiveImpersonationResponse, AdminWorkspaceMemberListItem
from app.services.audit_service import record_audit


async def get_active_session(
    session: AsyncSession,
    *,
    actor_user_id: UUID,
) -> ImpersonationSessionORM | None:
    return await session.scalar(
        select(ImpersonationSessionORM).where(
            ImpersonationSessionORM.actor_user_id == actor_user_id,
            ImpersonationSessionORM.ended_at.is_(None),
        )
    )


async def get_active_impersonation_status(
    session: AsyncSession,
    *,
    actor_user_id: UUID,
) -> ActiveImpersonationResponse:
    active_session = await get_active_session(session, actor_user_id=actor_user_id)
    if active_session is None:
        return ActiveImpersonationResponse(active=False)

    target = await session.get(UserORM, active_session.target_user_id)
    return ActiveImpersonationResponse(
        active=True,
        target_user_id=active_session.target_user_id,
        target_email=target.email if target else None,
        reason=active_session.reason,
        started_at=active_session.started_at,
    )


async def _validate_impersonation_target(session: AsyncSession, *, target_user_id: UUID) -> UserORM:
    target = await session.get(UserORM, target_user_id)
    if target is None:
        raise NotFoundError("User not found")

    if target.platform_role == PlatformRole.super_admin:
        raise ForbiddenError(
            message="Cannot impersonate platform administrators",
            error_code="impersonation_forbidden",
        )

    if target.status != UserStatus.active:
        raise ForbiddenError(
            message="Cannot impersonate users who are not active",
            error_code="impersonation_forbidden",
        )

    return target


async def start_impersonation(
    session: AsyncSession,
    *,
    actor_user_id: UUID,
    target_user_id: UUID,
    reason: str,
) -> ActiveImpersonationResponse:
    trimmed_reason = reason.strip()
    if len(trimmed_reason) < 10:
        raise ValidationError(message="Reason must be at least 10 characters", field="reason")

    if actor_user_id == target_user_id:
        raise ValidationError(message="Cannot impersonate yourself", field="user_id")

    existing = await get_active_session(session, actor_user_id=actor_user_id)
    if existing is not None:
        raise ConflictError(
            message="An impersonation session is already active",
            error_code="impersonation_active",
        )

    target = await _validate_impersonation_target(session, target_user_id=target_user_id)

    row = ImpersonationSessionORM(
        actor_user_id=actor_user_id,
        target_user_id=target_user_id,
        reason=trimmed_reason,
    )
    session.add(row)
    await session.flush()

    await record_audit(
        session,
        actor_user_id=actor_user_id,
        workspace_id=None,
        action="platform.impersonation.started",
        resource_type="user",
        resource_id=str(target_user_id),
        metadata={
            "target_email": target.email,
            "reason": trimmed_reason,
        },
    )

    return ActiveImpersonationResponse(
        active=True,
        target_user_id=target_user_id,
        target_email=target.email,
        reason=trimmed_reason,
        started_at=row.started_at,
    )


async def stop_impersonation(
    session: AsyncSession,
    *,
    actor_user_id: UUID,
) -> ActiveImpersonationResponse:
    active_session = await get_active_session(session, actor_user_id=actor_user_id)
    if active_session is None:
        raise NotFoundError(
            message="No active impersonation session",
            error_code="impersonation_not_active",
        )

    from app.models.base import utc_now

    active_session.ended_at = utc_now()
    await session.flush()

    await record_audit(
        session,
        actor_user_id=actor_user_id,
        workspace_id=None,
        action="platform.impersonation.stopped",
        resource_type="user",
        resource_id=str(active_session.target_user_id),
        metadata={"target_user_id": str(active_session.target_user_id)},
    )

    return ActiveImpersonationResponse(active=False)


async def list_workspace_members_for_admin(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    params: CursorParams,
) -> CursorResponse[AdminWorkspaceMemberListItem]:
    workspace = await session.get(WorkspaceORM, workspace_id)
    if workspace is None:
        raise NotFoundError("Workspace not found")

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
                & (WorkspaceMembershipORM.id < cursor_id)
            )
        )

    stmt = stmt.order_by(
        WorkspaceMembershipORM.created_at.desc(),
        WorkspaceMembershipORM.id.desc(),
    ).limit(params.limit + 1)

    result = await session.execute(stmt)
    rows = list(result.all())

    has_next = len(rows) > params.limit
    if has_next:
        rows = rows[: params.limit]

    items = [
        AdminWorkspaceMemberListItem(
            user_id=user.id,
            email=user.email,
            full_name=user.full_name,
            status=user.status,
            role=membership.role,
            joined_at=membership.created_at,
        )
        for membership, user in rows
    ]

    next_cursor = None
    if has_next and rows:
        last_membership, _ = rows[-1]
        next_cursor = encode_cursor(last_membership.created_at, last_membership.id)

    return CursorResponse(
        items=items,
        cursor=CursorMeta(next_cursor=next_cursor, has_next=has_next),
    )
