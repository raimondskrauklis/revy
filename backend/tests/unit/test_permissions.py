# backend/tests/unit/test_permissions.py
"""RBAC + tenancy matrix — mirror app/core/permissions.py."""
import uuid

import pytest

from app.constants.enums import AppRole, PlatformRole
from app.core.auth import CurrentUser
from app.core.exceptions import ForbiddenError
from app.core.permissions import (
    Permission,
    has_permission,
    require_any_permission,
    require_permission,
)
from app.core.tenancy import require_same_workspace


def test_platform_super_admin_has_all_permissions():
    user = CurrentUser(
        sub="sa",
        platform_role=PlatformRole.super_admin,
    )
    for perm in Permission:
        assert has_permission(None, perm, user=user)


def test_workspace_admin_cannot_manage_workspaces():
    assert not has_permission(AppRole.admin, Permission.admin_workspaces)


def test_viewer_cannot_manage():
    assert not has_permission(AppRole.viewer, Permission.items_manage)


def test_require_any_permission_super_admin_bypass():
    user = CurrentUser(sub="sa", platform_role=PlatformRole.super_admin)
    require_any_permission(user, {Permission.items_manage, Permission.admin_system})


def test_require_permission_raises_forbidden():
    user = CurrentUser(
        sub="u1",
        role=AppRole.viewer,
        workspace_id=uuid.uuid4(),
    )
    with pytest.raises(ForbiddenError):
        require_permission(user, Permission.items_manage)


def test_super_admin_cross_workspace_access():
    user = CurrentUser(sub="sa", platform_role=PlatformRole.super_admin)
    require_same_workspace(user, uuid.uuid4())


def test_member_denied_other_workspace():
    ws_a = uuid.uuid4()
    ws_b = uuid.uuid4()
    user = CurrentUser(sub="u1", role=AppRole.admin, workspace_id=ws_a)
    with pytest.raises(ForbiddenError):
        require_same_workspace(user, ws_b)
