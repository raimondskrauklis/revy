# backend/app/models/users.py
"""User identity ORM — TimestampedModel; lifecycle via UserStatus (not deleted_at)."""
from __future__ import annotations

from sqlalchemy import Enum, String
from sqlalchemy.orm import Mapped, mapped_column

from app.constants.enums import PlatformRole, UserStatus
from app.models.base import TimestampedModel


class UserORM(TimestampedModel):
    __tablename__ = "users"

    keycloak_user_id: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    email: Mapped[str] = mapped_column(String(320), unique=True, nullable=False)
    full_name: Mapped[str | None] = mapped_column(String(255), nullable=True)
    status: Mapped[UserStatus] = mapped_column(
        Enum(UserStatus, name="user_status", native_enum=True),
        nullable=False,
    )
    platform_role: Mapped[PlatformRole | None] = mapped_column(
        Enum(PlatformRole, name="platform_role", native_enum=True),
        nullable=True,
    )
    locale: Mapped[str] = mapped_column(String(16), nullable=False, default="en", server_default="en")
    timezone: Mapped[str] = mapped_column(String(64), nullable=False, default="UTC", server_default="UTC")

    @property
    def is_super_admin(self) -> bool:
        return self.platform_role == PlatformRole.super_admin
