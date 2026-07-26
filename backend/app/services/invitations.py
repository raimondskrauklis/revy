# backend/app/services/invitations.py
"""Workspace member invitations — INVITATIONS.md.

Invitees must be provisioned in PostgreSQL (JIT login or KC webhook) before
``accept_invitation`` — the invite only reserves email + workspace role.
"""
from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import AppRole, InvitationStatus, UserStatus
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.core.pagination import (
    CursorMeta,
    CursorParams,
    CursorResponse,
    InvalidCursorError,
    decode_cursor,
    encode_cursor,
)
from app.models.invitations import WorkspaceInvitationORM
from app.models.users import UserORM
from app.models.workspace_memberships import WorkspaceMembershipORM
from app.models.workspaces import WorkspaceORM
from app.schemas.invitations import InvitationListItem
from app.services.audit_service import record_audit

INVITATION_TTL_DAYS = 7

_INVITATION_ACCEPT_BLOCKED_STATUSES = frozenset(
    {
        UserStatus.pending_activation,
        UserStatus.pending_email_verification,
        UserStatus.pending_profile,
        UserStatus.pending_approval,
        UserStatus.rejected,
        UserStatus.suspended,
    }
)


def _generate_token() -> str:
    return secrets.token_urlsafe(32)


def invitation_to_payload(invitation: WorkspaceInvitationORM) -> dict:
    return {
        "email": invitation.email,
        "role": invitation.role.value,
        "token": invitation.token,
        "expires_at": invitation.expires_at.isoformat(),
        "invited_by_user_id": str(invitation.invited_by_user_id),
        "workspace_id": str(invitation.workspace_id),
        "status": invitation.status,
    }


async def create_invitation(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    email: str,
    role: AppRole,
    invited_by_user_id: UUID,
    impersonator_user_id: UUID | None = None,
) -> WorkspaceInvitationORM:
    """Create a pending workspace_invitations row."""
    normalized = email.strip().lower()
    if not normalized or "@" not in normalized:
        raise ValidationError(message="Invalid email", field="email")

    existing_user = await session.scalar(select(UserORM).where(UserORM.email.ilike(normalized)))
    if existing_user is not None:
        membership = await session.scalar(
            select(WorkspaceMembershipORM).where(
                WorkspaceMembershipORM.user_id == existing_user.id,
                WorkspaceMembershipORM.workspace_id == workspace_id,
            )
        )
        if membership is not None:
            raise ConflictError(message="User is already a workspace member")

    workspace = await session.scalar(
        select(WorkspaceORM).where(WorkspaceORM.id == workspace_id).with_for_update()
    )
    if workspace is None:
        raise NotFoundError("Workspace not found")

    now = datetime.now(UTC)
    pending_invite = await session.scalar(
        select(WorkspaceInvitationORM)
        .where(
            WorkspaceInvitationORM.workspace_id == workspace_id,
            func.lower(WorkspaceInvitationORM.email) == normalized,
            WorkspaceInvitationORM.status == InvitationStatus.pending,
            WorkspaceInvitationORM.expires_at > now,
        )
        .with_for_update()
    )
    if pending_invite is not None:
        raise ConflictError(message="A pending invitation already exists for this email")

    token = _generate_token()
    expires_at = now + timedelta(days=INVITATION_TTL_DAYS)
    invitation = WorkspaceInvitationORM(
        workspace_id=workspace_id,
        email=normalized,
        role=role,
        token=token,
        invited_by_user_id=invited_by_user_id,
        status=InvitationStatus.pending,
        expires_at=expires_at,
    )
    session.add(invitation)
    await session.flush()

    await record_audit(
        session,
        actor_user_id=invited_by_user_id,
        impersonator_user_id=impersonator_user_id,
        workspace_id=workspace_id,
        action="workspace_invitation.created",
        resource_type="workspace_invitation",
        resource_id=str(invitation.id),
        metadata={
            "invitation_id": str(invitation.id),
            "email": invitation.email,
            "role": invitation.role.value,
        },
    )

    return invitation


async def accept_invitation(
    session: AsyncSession,
    *,
    token: str,
    user: UserORM,
) -> WorkspaceMembershipORM:
    """Accept invitation — lookup token, create membership, mark accepted."""
    normalized_token = token.strip()
    if not normalized_token:
        raise ValidationError(message="Invitation token required", field="token")

    invitation = await session.scalar(
        select(WorkspaceInvitationORM)
        .where(WorkspaceInvitationORM.token == normalized_token)
        .with_for_update()
    )
    if invitation is None:
        raise NotFoundError("Invitation not found or expired")

    now = datetime.now(UTC)
    if invitation.status != InvitationStatus.pending:
        raise NotFoundError("Invitation not found or expired")
    if invitation.expires_at <= now:
        raise NotFoundError("Invitation not found or expired")

    if user.email.strip().lower() != invitation.email:
        raise ForbiddenError(message="Invitation email does not match your account")

    if user.status in _INVITATION_ACCEPT_BLOCKED_STATUSES:
        raise ForbiddenError(message="Account cannot accept invitations in current status")

    existing_membership = await session.scalar(
        select(WorkspaceMembershipORM).where(
            WorkspaceMembershipORM.user_id == user.id,
            WorkspaceMembershipORM.workspace_id == invitation.workspace_id,
        )
    )
    if existing_membership is not None:
        raise ConflictError(message="User is already a workspace member")

    membership = WorkspaceMembershipORM(
        user_id=user.id,
        workspace_id=invitation.workspace_id,
        role=invitation.role,
    )
    session.add(membership)

    invitation.status = InvitationStatus.accepted
    invitation.accepted_at = now

    await session.flush()
    return membership


async def list_invitations(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    params: CursorParams,
    status: InvitationStatus | None = InvitationStatus.pending,
) -> CursorResponse[InvitationListItem]:
    stmt = select(WorkspaceInvitationORM).where(WorkspaceInvitationORM.workspace_id == workspace_id)
    if status is not None:
        stmt = stmt.where(WorkspaceInvitationORM.status == status)
        if status == InvitationStatus.pending:
            now = datetime.now(UTC)
            stmt = stmt.where(WorkspaceInvitationORM.expires_at > now)

    if params.cursor:
        try:
            cursor_ts, cursor_id = decode_cursor(params.cursor)
        except InvalidCursorError as exc:
            raise ValidationError(message="Invalid cursor", field="cursor") from exc
        stmt = stmt.where(
            (WorkspaceInvitationORM.created_at < cursor_ts)
            | (
                (WorkspaceInvitationORM.created_at == cursor_ts)
                & (WorkspaceInvitationORM.id < cursor_id)
            )
        )

    stmt = stmt.order_by(
        WorkspaceInvitationORM.created_at.desc(),
        WorkspaceInvitationORM.id.desc(),
    ).limit(params.limit + 1)
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
        items=[InvitationListItem.model_validate(row) for row in rows],
        cursor=CursorMeta(next_cursor=next_cursor, has_next=has_next),
    )


async def revoke_invitation(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    invitation_id: UUID,
    actor_user_id: UUID | None = None,
    impersonator_user_id: UUID | None = None,
) -> WorkspaceInvitationORM:
    invitation = await session.scalar(
        select(WorkspaceInvitationORM).where(
            WorkspaceInvitationORM.id == invitation_id,
            WorkspaceInvitationORM.workspace_id == workspace_id,
        )
    )
    if invitation is None or invitation.status != InvitationStatus.pending:
        raise NotFoundError("Invitation not found")

    invitation.status = InvitationStatus.revoked
    await session.flush()

    if actor_user_id is not None:
        await record_audit(
            session,
            actor_user_id=actor_user_id,
            impersonator_user_id=impersonator_user_id,
            workspace_id=workspace_id,
            action="workspace_invitation.revoked",
            resource_type="workspace_invitation",
            resource_id=str(invitation_id),
            metadata={"invitation_id": str(invitation_id), "email": invitation.email},
        )

    return invitation
