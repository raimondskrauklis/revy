# backend/app/services/users.py
"""User lookup, bootstrap activation, /me assembly — ME_ENDPOINT.md."""
from __future__ import annotations

from uuid import UUID
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import AppRole, PlatformRole, UserStatus, WorkspaceStatus
from app.core.config import settings
from app.core.exceptions import ForbiddenError, NotFoundError, UnauthorizedError, ValidationError
from app.core.logging import get_logger
from app.models.users import UserORM
from app.models.workspace_memberships import WorkspaceMembershipORM
from app.models.workspaces import WorkspaceORM
from app.schemas.me import MeImpersonationInfo, MeMembership, MeResponse, MeUpdate
from app.services.billing import effective_plan
from app.services.onboarding import activate_user_with_workspace

logger = get_logger(__name__)

SUPPORTED_LOCALES = frozenset({"en", "lv"})
_ME_PATCH_BLOCKED_STATUSES = frozenset(
    {
        UserStatus.pending_activation,
        UserStatus.pending_email_verification,
        UserStatus.pending_profile,
        UserStatus.pending_approval,
        UserStatus.rejected,
        UserStatus.suspended,
    }
)

BOOTSTRAP_KEYCLOAK_PLACEHOLDER = "bootstrap-pending-first-login"


async def get_user_by_keycloak_id(session: AsyncSession, sub: str) -> UserORM | None:
    return await session.scalar(select(UserORM).where(UserORM.keycloak_user_id == sub))


async def get_user_by_email(session: AsyncSession, email: str) -> UserORM | None:
    return await session.scalar(select(UserORM).where(UserORM.email.ilike(email.strip())))


async def ensure_user_from_token(
    session: AsyncSession,
    *,
    sub: str,
    email: str | None,
    email_verified: bool,
) -> UserORM | None:
    """Deprecated — use ``provision_user_from_keycloak``."""
    from app.services.keycloak_provisioning import provision_user_from_keycloak

    try:
        return await provision_user_from_keycloak(
            session,
            sub=sub,
            email=email,
            email_verified=email_verified,
        )
    except UnauthorizedError as exc:
        if exc.error_code == "provision_email_required":
            return None
        raise


async def activate_bootstrap_super_admin(
    session: AsyncSession,
    user: UserORM,
    *,
    sub: str,
) -> UserORM:
    if user.platform_role != PlatformRole.super_admin:
        return user
    if user.status == UserStatus.active and user.keycloak_user_id == sub:
        return user

    bootstrap_email = (settings.bootstrap_super_admin_email or "").strip().lower()
    if bootstrap_email and user.email.lower() != bootstrap_email:
        return user

    user.keycloak_user_id = sub
    user.status = UserStatus.active
    await session.flush()
    logger.info(
        "bootstrap_super_admin_activated",
        extra={"user_id": str(user.id), "operation": "bootstrap_activation"},
    )
    return user


def _validate_timezone(timezone: str) -> str:
    if not timezone or not timezone.strip():
        raise ValidationError(message="Invalid timezone", field="timezone")
    try:
        ZoneInfo(timezone)
    except ZoneInfoNotFoundError as exc:
        raise ValidationError(message="Invalid timezone", field="timezone") from exc
    return timezone


async def update_me(
    session: AsyncSession,
    *,
    user_id: UUID,
    payload: MeUpdate,
) -> UserORM:
    user = await session.scalar(select(UserORM).where(UserORM.id == user_id).with_for_update())
    if user is None:
        raise NotFoundError("User not found")
    if user.status in _ME_PATCH_BLOCKED_STATUSES:
        raise ForbiddenError(message="User cannot update profile in current status")

    updates = payload.model_dump(exclude_unset=True)
    if not updates:
        return user

    if "full_name" in updates:
        full_name = updates["full_name"]
        user.full_name = full_name.strip() if full_name else None

    if "locale" in updates:
        locale = updates["locale"]
        if locale not in SUPPORTED_LOCALES:
            raise ValidationError(message="Unsupported locale", field="locale")
        user.locale = locale

    if "timezone" in updates:
        timezone = updates["timezone"]
        if timezone is None:
            raise ValidationError(message="Invalid timezone", field="timezone")
        user.timezone = _validate_timezone(timezone)

    await session.flush()
    return user


async def build_me_response(
    session: AsyncSession,
    user_id: UUID,
    *,
    impersonation: MeImpersonationInfo | None = None,
) -> MeResponse:
    user = await session.get(UserORM, user_id)
    if user is None:
        raise NotFoundError("User not found")

    membership_rows = (
        await session.execute(
            select(WorkspaceMembershipORM, WorkspaceORM)
            .join(WorkspaceORM, WorkspaceORM.id == WorkspaceMembershipORM.workspace_id)
            .where(
                WorkspaceMembershipORM.user_id == user.id,
                WorkspaceORM.status == WorkspaceStatus.active,
            )
            .order_by(WorkspaceORM.name.asc())
        )
    ).all()

    memberships = [
        MeMembership(
            workspace_id=membership.workspace_id,
            workspace_name=workspace.name,
            workspace_slug=workspace.slug,
            role=membership.role,
        )
        for membership, workspace in membership_rows
    ]

    active_workspace_id: UUID | None = None
    active_role: AppRole | None = None
    workspace_plan: str | None = None
    if len(memberships) == 1:
        active_workspace_id = memberships[0].workspace_id
        active_role = memberships[0].role
        _, workspace = membership_rows[0]
        workspace_plan = effective_plan(workspace)

    return MeResponse(
        id=user.id,
        email=user.email,
        full_name=user.full_name,
        status=user.status,
        platform_role=user.platform_role,
        locale=user.locale,
        timezone=user.timezone,
        workspace_id=active_workspace_id,
        role=active_role,
        workspace_plan=workspace_plan,
        memberships=memberships,
        impersonation=impersonation,
    )


async def set_active_workspace(
    session: AsyncSession,
    *,
    user_id: UUID,
    workspace_id: UUID,
) -> MeResponse:
    row = (
        await session.execute(
            select(WorkspaceMembershipORM, WorkspaceORM)
            .join(WorkspaceORM, WorkspaceORM.id == WorkspaceMembershipORM.workspace_id)
            .where(
                WorkspaceMembershipORM.user_id == user_id,
                WorkspaceMembershipORM.workspace_id == workspace_id,
                WorkspaceORM.status == WorkspaceStatus.active,
            )
        )
    ).first()
    if row is None:
        raise ForbiddenError(message="Workspace access denied")

    membership, workspace = row
    me = await build_me_response(session, user_id)
    return me.model_copy(
        update={
            "workspace_id": workspace_id,
            "role": membership.role,
            "workspace_plan": effective_plan(workspace),
        }
    )


async def list_pending_users(session: AsyncSession) -> list[UserORM]:
    return list(
        await session.scalars(
            select(UserORM)
            .where(UserORM.status == UserStatus.pending_approval)
            .order_by(UserORM.created_at.asc())
        )
    )


async def approve_pending_user(session: AsyncSession, user_id: UUID) -> UserORM:
    user = await session.scalar(
        select(UserORM).where(UserORM.id == user_id).with_for_update()
    )
    if user is None:
        raise NotFoundError("User not found")
    if user.status != UserStatus.pending_approval:
        raise ValidationError("User is not pending approval")

    display_name = (user.full_name or user.email).strip()
    await activate_user_with_workspace(session, user, name=display_name)
    return user


async def reject_pending_user(session: AsyncSession, user_id: UUID) -> UserORM:
    user = await session.scalar(
        select(UserORM).where(UserORM.id == user_id).with_for_update()
    )
    if user is None:
        raise NotFoundError("User not found")
    if user.status != UserStatus.pending_approval:
        raise ValidationError("User is not pending approval")

    user.status = UserStatus.rejected
    await session.flush()
    return user
