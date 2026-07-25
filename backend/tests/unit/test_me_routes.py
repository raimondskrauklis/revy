# backend/tests/unit/test_me_routes.py
"""GET /me route — workspace_plan from active workspace header context."""
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.api.v1.me import _build_current_me
from app.constants.enums import AppRole, UserStatus
from app.core.auth import CurrentUser
from app.models.workspaces import WorkspaceORM


@pytest.mark.asyncio
async def test_build_current_me_sets_workspace_plan_from_header_workspace():
    workspace_id = uuid.uuid4()
    user_id = uuid.uuid4()
    workspace = WorkspaceORM(slug="acme", name="Acme", plan="pro")
    workspace.id = workspace_id

    current_user = CurrentUser(
        sub="sub",
        actor_user_id=user_id,
        workspace_id=workspace_id,
        role=AppRole.admin,
    )
    session = AsyncMock()
    session.get = AsyncMock(return_value=workspace)

    with patch("app.api.v1.me.build_me_response", AsyncMock()) as build_me:
        build_me.return_value = build_me.return_value
        from app.schemas.me import MeResponse

        build_me.return_value = MeResponse(
            id=user_id,
            email="user@example.com",
            full_name="User",
            status=UserStatus.active,
            platform_role=None,
            workspace_id=None,
            role=None,
            locale="en",
            timezone="UTC",
            memberships=[],
            workspace_plan=None,
        )

        me = await _build_current_me(session, current_user)

    assert me.workspace_id == workspace_id
    assert me.workspace_plan == "pro"
