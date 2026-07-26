# backend/app/services/keycloak_provisioning.py
"""Keycloak identity → PostgreSQL user provisioning — USER_PROVISIONING program.

JIT auth and KC webhooks call ``provision_user_from_keycloak`` (idempotent).
Invitees must be provisioned (JIT or webhook) before ``accept_invitation``.
"""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import PlatformRole, UserStatus
from app.core.config import settings
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.logging import get_logger
from app.models.users import UserORM
from app.services.onboarding import (
    maybe_auto_provision_user,
    resolve_initial_user_status,
)
from app.services.users import (
    BOOTSTRAP_KEYCLOAK_PLACEHOLDER,
    activate_bootstrap_super_admin,
    get_user_by_email,
    get_user_by_keycloak_id,
)

logger = get_logger(__name__)


def normalize_email(email: str) -> str:
    return email.strip().lower()


async def _assert_email_available(
    session: AsyncSession,
    email: str,
    *,
    excluding_user_id: UUID | None,
) -> None:
    existing = await get_user_by_email(session, email)
    if existing is None:
        return
    if excluding_user_id is not None and existing.id == excluding_user_id:
        return
    raise ConflictError(
        message="Email is already associated with another account",
        error_code="identity_email_conflict",
    )


async def _sync_user_email(
    session: AsyncSession,
    user: UserORM,
    email: str,
    *,
    email_verified: bool,
) -> None:
    if user.email == email:
        if email_verified and user.status == UserStatus.pending_email_verification:
            user.status = resolve_initial_user_status(email_verified=True)
            await session.flush()
        return

    await _assert_email_available(session, email, excluding_user_id=user.id)
    user.email = email
    if email_verified and user.status == UserStatus.pending_email_verification:
        user.status = resolve_initial_user_status(email_verified=True)
    await session.flush()


async def _find_bootstrap_seed(session: AsyncSession, email: str) -> UserORM | None:
    bootstrap_email = (settings.bootstrap_super_admin_email or "").strip().lower()
    if not bootstrap_email or email != bootstrap_email:
        return None
    seeded = await get_user_by_email(session, bootstrap_email)
    if seeded is None:
        return None
    if seeded.platform_role != PlatformRole.super_admin:
        return None
    if seeded.status not in (UserStatus.pending_activation, UserStatus.active):
        return None
    return seeded


async def provision_user_from_keycloak(
    session: AsyncSession,
    *,
    sub: str,
    email: str | None,
    email_verified: bool,
    display_name: str | None = None,
) -> UserORM:
    """Create or update app user from Keycloak identity claims."""
    if not email or not email.strip():
        raise UnauthorizedError(
            "User not provisioned",
            error_code="provision_email_required",
        )

    normalized = normalize_email(email)
    user = await get_user_by_keycloak_id(session, sub)
    if user is not None:
        await _sync_user_email(session, user, normalized, email_verified=email_verified)
        user = await maybe_auto_provision_user(
            session,
            user,
            display_name=display_name,
            email_verified=email_verified,
        )
        return await activate_bootstrap_super_admin(session, user, sub=sub)

    seeded = await _find_bootstrap_seed(session, normalized)
    if seeded is not None:
        return await activate_bootstrap_super_admin(session, seeded, sub=sub)

    await _assert_email_available(session, normalized, excluding_user_id=None)

    user = UserORM(
        keycloak_user_id=sub,
        email=normalized,
        status=resolve_initial_user_status(email_verified=email_verified),
    )
    session.add(user)
    await session.flush()
    logger.info(
        "user_provisioned",
        extra={"user_id": str(user.id), "operation": "provision_user_from_keycloak"},
    )

    user = await maybe_auto_provision_user(
        session,
        user,
        display_name=display_name,
        email_verified=email_verified,
    )
    return await activate_bootstrap_super_admin(session, user, sub=sub)


async def apply_keycloak_user_disabled(
    session: AsyncSession,
    *,
    sub: str,
    enabled: bool,
) -> UserORM | None:
    user = await get_user_by_keycloak_id(session, sub)
    if user is None:
        return None
    if enabled:
        if user.status == UserStatus.suspended:
            user.status = UserStatus.active
    else:
        user.status = UserStatus.suspended
    await session.flush()
    return user


async def apply_keycloak_user_deleted(session: AsyncSession, *, sub: str) -> UserORM | None:
    user = await get_user_by_keycloak_id(session, sub)
    if user is None:
        return None
    user.status = UserStatus.deleted
    if user.keycloak_user_id != BOOTSTRAP_KEYCLOAK_PLACEHOLDER:
        user.keycloak_user_id = f"deleted:{sub}"
    await session.flush()
    return user
