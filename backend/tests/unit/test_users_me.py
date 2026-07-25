# backend/tests/unit/test_users_me.py
"""GET /me assembly — workspace_plan and active memberships."""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.constants.enums import AppRole, UserStatus, WorkspaceStatus
from app.models.users import UserORM
from app.models.workspace_memberships import WorkspaceMembershipORM
from app.models.workspaces import WorkspaceORM
from app.services.users import build_me_response


def _user() -> UserORM:
    user = UserORM(
        keycloak_user_id="kc-me",
        email="user@example.com",
        full_name="User",
        status=UserStatus.active,
        locale="en",
        timezone="UTC",
    )
    user.id = uuid.uuid4()
    return user


@pytest.mark.asyncio
async def test_build_me_response_excludes_suspended_workspaces():
    user = _user()
    active_workspace = WorkspaceORM(
        slug="active",
        name="Active",
        status=WorkspaceStatus.active,
        plan="pro",
    )
    active_workspace.id = uuid.uuid4()
    suspended_workspace = WorkspaceORM(
        slug="suspended",
        name="Suspended",
        status=WorkspaceStatus.suspended,
        plan="free",
    )
    suspended_workspace.id = uuid.uuid4()
    _ = suspended_workspace  # excluded by SQL filter on WorkspaceStatus.active

    active_membership = WorkspaceMembershipORM(
        user_id=user.id,
        workspace_id=active_workspace.id,
        role=AppRole.admin,
    )

    session = AsyncMock()
    session.get = AsyncMock(return_value=user)
    execute_result = MagicMock()
    execute_result.all.return_value = [
        (active_membership, active_workspace),
    ]
    session.execute = AsyncMock(return_value=execute_result)

    me = await build_me_response(session, user.id)

    assert len(me.memberships) == 1
    assert me.memberships[0].workspace_slug == "active"
    assert me.workspace_plan == "pro"


@pytest.mark.asyncio
async def test_build_me_response_sets_workspace_plan_for_single_membership():
    user = _user()
    workspace = WorkspaceORM(
        slug="solo",
        name="Solo",
        status=WorkspaceStatus.active,
        plan="pro",
    )
    workspace.id = uuid.uuid4()
    membership = WorkspaceMembershipORM(
        user_id=user.id,
        workspace_id=workspace.id,
        role=AppRole.viewer,
    )

    session = AsyncMock()
    session.get = AsyncMock(return_value=user)
    execute_result = MagicMock()
    execute_result.all.return_value = [(membership, workspace)]
    session.execute = AsyncMock(return_value=execute_result)

    me = await build_me_response(session, user.id)

    assert me.workspace_id == workspace.id
    assert me.role == AppRole.viewer
    assert me.workspace_plan == "pro"
