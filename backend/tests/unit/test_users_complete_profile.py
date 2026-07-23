# backend/tests/unit/test_users_complete_profile.py
"""POST /users/complete-profile service logic."""
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import uuid4

import pytest

from app.constants.enums import UserStatus
from app.core.exceptions import ConflictError, ForbiddenError
from app.models.users import UserORM
from app.services.onboarding import complete_user_profile


@pytest.mark.asyncio
async def test_complete_profile_mode_a_activates_user():
    user_id = uuid4()
    user = UserORM(
        keycloak_user_id="kc-1",
        email="user@example.com",
        status=UserStatus.pending_profile,
    )
    user.id = user_id

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=user)
    session.flush = AsyncMock()
    session.add = MagicMock()

    with (
        patch("app.services.onboarding.settings.registration_require_admin_approval", False),
        patch(
            "app.services.onboarding.activate_user_with_workspace",
            new_callable=AsyncMock,
        ) as activate,
    ):
        result = await complete_user_profile(session, user_id, full_name="Ada Lovelace")

    assert result.full_name == "Ada Lovelace"
    activate.assert_awaited_once()
    assert activate.await_args.kwargs["name"] == "Ada Lovelace"


@pytest.mark.asyncio
async def test_complete_profile_mode_b_pending_approval():
    user_id = uuid4()
    user = UserORM(
        keycloak_user_id="kc-2",
        email="pending@example.com",
        status=UserStatus.pending_profile,
    )
    user.id = user_id

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=user)
    session.flush = AsyncMock()

    with patch("app.services.onboarding.settings.registration_require_admin_approval", True):
        result = await complete_user_profile(session, user_id, full_name="Test User")

    assert result.status == UserStatus.pending_approval
    assert result.full_name == "Test User"


@pytest.mark.asyncio
async def test_complete_profile_rejects_active_user():
    user_id = uuid4()
    user = UserORM(
        keycloak_user_id="kc-3",
        email="active@example.com",
        status=UserStatus.active,
    )
    user.id = user_id

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=user)

    with pytest.raises(ConflictError):
        await complete_user_profile(session, user_id, full_name="Name")


@pytest.mark.asyncio
async def test_complete_profile_rejects_wrong_status():
    user_id = uuid4()
    user = UserORM(
        keycloak_user_id="kc-4",
        email="wait@example.com",
        status=UserStatus.pending_approval,
    )
    user.id = user_id

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=user)

    with pytest.raises(ForbiddenError):
        await complete_user_profile(session, user_id, full_name="Name")
