# backend/app/core/tenancy.py
"""Workspace (tenant) scoping — see docs/backend/TENANCY.md."""
from uuid import UUID

from app.constants.enums import PlatformRole
from app.core.exceptions import ForbiddenError


def is_platform_admin(user) -> bool:
    platform_role = getattr(user, "platform_role", None)
    if platform_role == PlatformRole.super_admin:
        return True
    return bool(getattr(user, "is_super_admin", False))


def require_same_workspace(
    user,
    resource_workspace_id: UUID,
    *,
    message: str = "Workspace access denied",
) -> None:
    if is_platform_admin(user):
        return
    workspace_id = getattr(user, "workspace_id", None)
    if workspace_id is None or workspace_id != resource_workspace_id:
        raise ForbiddenError(message=message, error_code="forbidden")


def require_workspace(user, *, message: str = "No active workspace") -> UUID:
    """Tenant routes: non–platform user must have active workspace_id on CurrentUser."""
    if is_platform_admin(user):
        raise ForbiddenError(
            message="Platform admin must specify target workspace explicitly",
            error_code="validation_error",
        )
    workspace_id = getattr(user, "workspace_id", None)
    if workspace_id is None:
        raise ForbiddenError(message=message, error_code="forbidden")
    return workspace_id


def workspace_id_for_create(user) -> UUID:
    """Workspace for new tenant-owned rows — never trust client-supplied workspace_id."""
    return require_workspace(user)
