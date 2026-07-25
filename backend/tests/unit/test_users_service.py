# backend/tests/unit/test_users_service.py
"""User profile service — ME_ENDPOINT.md W1."""
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest

from app.constants.enums import UserStatus
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.models.users import UserORM
from app.schemas.me import MeUpdate
from app.services.users import build_me_response, update_me


def _active_user() -> UserORM:
    user = UserORM(
        keycloak_user_id="kc-1",
        email="user@example.com",
        full_name="Ada",
        status=UserStatus.active,
        locale="en",
        timezone="UTC",
    )
    user.id = uuid4()
    return user


@pytest.mark.asyncio
async def test_update_me_changes_profile_fields():
    user = _active_user()
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=user)
    session.flush = AsyncMock()

    updated = await update_me(
        session,
        user_id=user.id,
        payload=MeUpdate(full_name="Ada Lovelace", locale="lv", timezone="Europe/Riga"),
    )

    assert updated.full_name == "Ada Lovelace"
    assert updated.locale == "lv"
    assert updated.timezone == "Europe/Riga"


@pytest.mark.asyncio
async def test_update_me_partial_patch_leaves_unset_fields():
    user = _active_user()
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=user)
    session.flush = AsyncMock()

    await update_me(session, user_id=user.id, payload=MeUpdate(locale="lv"))

    assert user.full_name == "Ada"
    assert user.locale == "lv"
    assert user.timezone == "UTC"


@pytest.mark.asyncio
async def test_update_me_rejects_unsupported_locale():
    user = _active_user()
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=user)

    with pytest.raises(ValidationError, match="Unsupported locale"):
        await update_me(session, user_id=user.id, payload=MeUpdate(locale="de"))


@pytest.mark.asyncio
async def test_update_me_rejects_invalid_timezone():
    user = _active_user()
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=user)

    with pytest.raises(ValidationError, match="Invalid timezone"):
        await update_me(session, user_id=user.id, payload=MeUpdate(timezone="Not/AZone"))


@pytest.mark.asyncio
async def test_update_me_rejects_null_timezone():
    user = _active_user()
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=user)

    with pytest.raises(ValidationError, match="Invalid timezone"):
        await update_me(session, user_id=user.id, payload=MeUpdate(timezone=None))


@pytest.mark.asyncio
async def test_update_me_rejects_suspended_user():
    user = _active_user()
    user.status = UserStatus.suspended
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=user)

    with pytest.raises(ForbiddenError):
        await update_me(session, user_id=user.id, payload=MeUpdate(full_name="Name"))


@pytest.mark.asyncio
async def test_update_me_not_found():
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)

    with pytest.raises(NotFoundError):
        await update_me(session, user_id=uuid4(), payload=MeUpdate(full_name="Name"))


@pytest.mark.asyncio
async def test_build_me_response_includes_locale_and_timezone():
    user = _active_user()
    session = AsyncMock()
    session.get = AsyncMock(return_value=user)
    execute_result = MagicMock()
    execute_result.all.return_value = []
    session.execute = AsyncMock(return_value=execute_result)

    me = await build_me_response(session, user.id)

    assert me.locale == "en"
    assert me.timezone == "UTC"
