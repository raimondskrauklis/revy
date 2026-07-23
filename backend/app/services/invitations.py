# backend/app/services/invitations.py
"""Workspace member invitations — docs/backend/INVITATIONS.md."""
from __future__ import annotations

import secrets
from datetime import UTC, datetime, timedelta
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import AppRole
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.models.users import UserORM
from app.models.workspace_memberships import WorkspaceMembershipORM

INVITATION_TTL_DAYS = 7


def _generate_token() -> str:
    return secrets.token_urlsafe(32)


async def create_invitation(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    email: str,
    role: AppRole,
    invited_by_user_id: UUID,
) -> dict:
    """Persist invitation row when `workspace_invitations` table exists (P1 migration)."""
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

    token = _generate_token()
    expires_at = datetime.now(UTC) + timedelta(days=INVITATION_TTL_DAYS)
    return {
        "email": normalized,
        "role": role.value,
        "token": token,
        "expires_at": expires_at.isoformat(),
        "invited_by_user_id": str(invited_by_user_id),
        "workspace_id": str(workspace_id),
    }


async def accept_invitation(
    session: AsyncSession,
    *,
    token: str,
    user: UserORM,
) -> WorkspaceMembershipORM:
    """Accept invitation — implement DB lookup when P1 table is added."""
    if not token.strip():
        raise ValidationError(message="Invitation token required", field="token")
    raise NotFoundError("Invitation not found or expired")
