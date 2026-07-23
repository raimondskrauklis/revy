# backend/app/core/permissions.py
"""RBAC — Permission enum + ROLE_PERMISSIONS matrix. See docs/backend/PERMISSIONS.md."""
from enum import Enum

from app.constants.enums import AppRole, PlatformRole
from app.core.exceptions import ForbiddenError
from app.core.logging import get_logger

logger = get_logger(__name__)


class Permission(str, Enum):
    """Domain permissions — extend per product."""

    items_view = "items:view"
    items_manage = "items:manage"
    admin_users = "admin:users"
    admin_workspaces = "admin:workspaces"
    admin_system = "admin:system"


ROLE_PERMISSIONS: dict[AppRole, set[Permission]] = {
    AppRole.admin: {
        Permission.items_view,
        Permission.items_manage,
        Permission.admin_users,
    },
    AppRole.operator: {
        Permission.items_view,
        Permission.items_manage,
    },
    AppRole.viewer: {
        Permission.items_view,
    },
}

PLATFORM_SUPER_ADMIN_PERMISSIONS: set[Permission] = set(Permission)


def _is_platform_super_admin(user) -> bool:
    if getattr(user, "is_super_admin", False):
        return True
    return getattr(user, "platform_role", None) == PlatformRole.super_admin


def has_permission(role: AppRole | None, permission: Permission, *, user=None) -> bool:
    if user is not None and _is_platform_super_admin(user):
        return True
    if role is None:
        return False
    return permission in ROLE_PERMISSIONS.get(role, set())


def has_any_permission(role: AppRole | None, permissions: set[Permission]) -> bool:
    if role is None:
        return False
    return bool(ROLE_PERMISSIONS.get(role, set()) & permissions)


def has_all_permissions(role: AppRole | None, permissions: set[Permission]) -> bool:
    if role is None:
        return False
    return permissions.issubset(ROLE_PERMISSIONS.get(role, set()))


def require_permission(user, permission: Permission) -> None:
    """Raise ForbiddenError if user lacks permission (workspace role or platform super_admin)."""
    role = getattr(user, "role", None)
    if _is_platform_super_admin(user):
        return
    if not has_permission(role, permission):
        logger.warning(
            "Permission denied",
            extra={
                "user_sub": getattr(user, "sub", None),
                "workspace_id": str(getattr(user, "workspace_id", None)),
                "role": role.value if role else None,
                "required": permission.value,
                "operation": "require_permission",
            },
        )
        raise ForbiddenError(
            message=f"Permission denied: {permission.value}",
            error_code="forbidden",
        )


def require_any_permission(user, permissions: set[Permission]) -> None:
    if _is_platform_super_admin(user):
        return
    role = getattr(user, "role", None)
    if not has_any_permission(role, permissions):
        names = ", ".join(p.value for p in permissions)
        raise ForbiddenError(
            message=f"Permission denied: need one of [{names}]",
            error_code="forbidden",
        )


def get_user_permissions(role: AppRole | None) -> set[Permission]:
    if role is None:
        return set()
    return ROLE_PERMISSIONS.get(role, set()).copy()
