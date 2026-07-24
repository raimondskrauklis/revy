# backend/tests/unit/test_admin_users.py
"""Admin signup queue — super_admin only."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.constants.enums import AppRole, PlatformRole, UserStatus
from app.core.auth import CurrentUser, require_super_admin
from app.core.exceptions import ForbiddenError
from app.models.users import UserORM
from app.services.users import approve_pending_user, list_pending_users, reject_pending_user


@pytest.mark.asyncio
async def test_require_super_admin_rejects_workspace_admin():
    guard = require_super_admin()
    user = CurrentUser(
        sub="u1",
        role=AppRole.admin,
        workspace_id=uuid.uuid4(),
    )
    with pytest.raises(ForbiddenError):
        await guard(user=user)


@pytest.mark.asyncio
async def test_require_super_admin_allows_platform_admin():
    guard = require_super_admin()
    user = CurrentUser(sub="sa", platform_role=PlatformRole.super_admin)
    assert await guard(user=user) is user


@pytest.mark.asyncio
async def test_list_pending_users_filters_status():
    pending = UserORM(
        keycloak_user_id="kc-p",
        email="pending@example.com",
        status=UserStatus.pending_approval,
    )
    session = AsyncMock()
    session.scalars = AsyncMock(return_value=[pending])

    users = await list_pending_users(session)
    assert users == [pending]


@pytest.mark.asyncio
async def test_approve_pending_user_activates():
    user_id = uuid.uuid4()
    user = UserORM(
        keycloak_user_id="kc-a",
        email="approve@example.com",
        full_name="Approve Me",
        status=UserStatus.pending_approval,
    )
    user.id = user_id

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=user)
    session.flush = AsyncMock()
    session.add = MagicMock()

    with patch(
        "app.services.users.activate_user_with_workspace",
        new_callable=AsyncMock,
    ) as activate:
        result = await approve_pending_user(session, user_id)

    activate.assert_awaited_once()
    assert result is user


@pytest.mark.asyncio
async def test_reject_pending_user_sets_rejected():
    user_id = uuid.uuid4()
    user = UserORM(
        keycloak_user_id="kc-r",
        email="reject@example.com",
        status=UserStatus.pending_approval,
    )
    user.id = user_id

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=user)
    session.flush = AsyncMock()

    result = await reject_pending_user(session, user_id)
    assert result.status == UserStatus.rejected
