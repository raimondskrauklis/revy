# backend/app/services/onboarding.py
"""User activation + workspace provisioning — USER_REGISTRATION.md."""
from __future__ import annotations

import re
import uuid
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import AppRole, UserStatus
from app.core.config import settings
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.users import UserORM
from app.models.workspace_memberships import WorkspaceMembershipORM
from app.models.workspaces import WorkspaceORM


def _slugify_workspace_name(name: str, *, fallback: str) -> str:
    base = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-") or fallback
    return f"{base}-{uuid.uuid4().hex[:8]}"


def resolve_initial_user_status(*, email_verified: bool) -> UserStatus:
    """Map registration config + Keycloak email state to initial ``user_status``."""
    if not email_verified:
        return UserStatus.pending_email_verification
    if settings.registration_require_profile_form:
        return UserStatus.pending_profile
    if settings.registration_require_admin_approval:
        return UserStatus.pending_approval
    return UserStatus.pending_profile


def should_auto_provision_user(*, email_verified: bool) -> bool:
    """Mode A open signup — provision workspace without profile form or admin gate."""
    if not email_verified:
        return False
    return not settings.registration_require_profile_form and not settings.registration_require_admin_approval


async def activate_user_with_workspace(
    session: AsyncSession,
    user: UserORM,
    *,
    name: str,
    role: AppRole = AppRole.admin,
) -> WorkspaceORM:
    """Create workspace + membership and set user active — Mode A auto or Mode B approve."""
    slug = _slugify_workspace_name(name, fallback="workspace")
    workspace = WorkspaceORM(slug=slug, name=name)
    session.add(workspace)
    await session.flush()

    session.add(
        WorkspaceMembershipORM(
            user_id=user.id,
            workspace_id=workspace.id,
            role=role,
        )
    )
    user.status = UserStatus.active
    await session.flush()
    return workspace


async def maybe_auto_provision_user(
    session: AsyncSession,
    user: UserORM,
    *,
    display_name: str | None,
    email_verified: bool,
) -> UserORM:
    """Open signup: create personal workspace when registration gates are off."""
    if user.status == UserStatus.active:
        return user
    if not should_auto_provision_user(email_verified=email_verified):
        return user
    if user.status not in (
        UserStatus.pending_profile,
        UserStatus.pending_email_verification,
        UserStatus.pending_approval,
    ):
        return user

    name = (display_name or user.full_name or user.email).strip()
    await activate_user_with_workspace(session, user, name=name)
    return user


async def complete_user_profile(
    session: AsyncSession,
    user_id: UUID,
    *,
    full_name: str,
) -> UserORM:
    """POST /users/complete-profile — Mode A activates; Mode B → pending_approval."""
    user = await session.scalar(
        select(UserORM).where(UserORM.id == user_id).with_for_update()
    )
    if user is None:
        raise NotFoundError("User not found")

    name = full_name.strip()
    if not name:
        raise ValidationError("Display name is required", field="full_name")

    if user.status == UserStatus.active:
        raise ConflictError("Profile already completed")
    if user.status != UserStatus.pending_profile:
        raise ForbiddenError(message="Profile completion not allowed in current status")

    user.full_name = name
    if settings.registration_require_admin_approval:
        user.status = UserStatus.pending_approval
        await session.flush()
        return user

    await activate_user_with_workspace(session, user, name=name)
    return user
