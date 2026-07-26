# backend/app/core/bootstrap.py
"""Bootstrap super-admin configuration guard — USER_PROVISIONING P3."""
from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import PlatformRole
from app.core.config import settings
from app.core.logging import get_logger
from app.models.users import UserORM

logger = get_logger(__name__)


class BootstrapConfigError(RuntimeError):
    """Raised when bootstrap env is set but the seed row is missing in production."""


async def validate_bootstrap_super_admin_config(session: AsyncSession) -> None:
    if settings.environment == "test":
        return

    email = (settings.bootstrap_super_admin_email or "").strip().lower()
    if not email:
        return

    seeded = await session.scalar(
        select(UserORM).where(
            UserORM.platform_role == PlatformRole.super_admin,
            UserORM.email.ilike(email),
        )
    )
    if seeded is not None:
        return

    message = (
        "BOOTSTRAP_SUPER_ADMIN_EMAIL is set but no matching super_admin seed row exists. "
        "Run: cd backend && pipenv run python scripts/seed_bootstrap_super_admin.py"
    )
    if settings.environment in {"production", "staging"}:
        raise BootstrapConfigError(message)

    logger.warning(
        "bootstrap_super_admin_seed_missing",
        extra={"email": email, "environment": settings.environment},
    )
