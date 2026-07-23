# backend/scripts/seed_bootstrap_super_admin.py
"""Bootstrap first platform super_admin — one-time per environment.

See docs/backend/BOOTSTRAP_SUPER_ADMIN.md.
"""
from __future__ import annotations

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import PlatformRole, UserStatus
from app.core.config import settings
from app.core.database import AsyncSessionLocal
from app.models.users import UserORM

BOOTSTRAP_KEYCLOAK_PLACEHOLDER = "bootstrap-pending-first-login"


async def bootstrap_super_admin(session: AsyncSession) -> bool:
    email = (settings.bootstrap_super_admin_email or "").strip().lower()
    if not email:
        print("❌ BOOTSTRAP_SUPER_ADMIN_EMAIL is not set")
        return False

    existing = await session.scalar(
        select(UserORM).where(
            UserORM.platform_role == PlatformRole.super_admin,
            UserORM.email.ilike(email),
        )
    )
    if existing:
        print("✅ Bootstrap super admin already exists — skipping")
        return False

    user = UserORM(
        keycloak_user_id=BOOTSTRAP_KEYCLOAK_PLACEHOLDER,
        email=email,
        full_name="System Administrator",
        platform_role=PlatformRole.super_admin,
        status=UserStatus.pending_activation,
    )
    session.add(user)
    await session.commit()
    await session.refresh(user)

    print("✅ Created bootstrap super admin (no workspace membership):")
    print(f"   - ID: {user.id}")
    print(f"   - Email: {user.email}")
    print("\n⚠️  Register same email in Keycloak → first login → remove BOOTSTRAP_SUPER_ADMIN_EMAIL")
    return True


async def main() -> None:
    async with AsyncSessionLocal() as session:
        await bootstrap_super_admin(session)
    print("\n✅ Bootstrap complete")


if __name__ == "__main__":
    asyncio.run(main())
