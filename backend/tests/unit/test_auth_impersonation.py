# backend/tests/unit/test_auth_impersonation.py
"""CurrentUser impersonation integration — W7."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.constants.enums import AppRole, PlatformRole, UserStatus, WorkspaceStatus
from app.core.auth import CurrentUser, require_impersonation_allowed
from app.core.exceptions import ForbiddenError
from app.models.impersonation_session import ImpersonationSessionORM
from app.models.users import UserORM
from app.models.workspace_memberships import WorkspaceMembershipORM
from app.models.workspaces import WorkspaceORM


def _user(
    *,
    status: UserStatus = UserStatus.active,
    platform_role: PlatformRole | None = None,
    email: str = "actor@example.com",
) -> UserORM:
    user = UserORM(
        keycloak_user_id="kc-actor",
        email=email,
        status=status,
        platform_role=platform_role,
    )
    user.id = uuid.uuid4()
    return user


def test_current_user_effective_and_impersonator_ids():
    actor_id = uuid.uuid4()
    target_id = uuid.uuid4()
    user = CurrentUser(
        sub="sub-1",
        actor_user_id=actor_id,
        impersonated_user_id=target_id,
        platform_role=PlatformRole.super_admin,
    )

    assert user.effective_user_id == target_id
    assert user.user_id == target_id
    assert user.impersonator_user_id == actor_id
    assert user.is_impersonating is True


def test_current_user_without_impersonation():
    actor_id = uuid.uuid4()
    user = CurrentUser(sub="sub-1", actor_user_id=actor_id)

    assert user.effective_user_id == actor_id
    assert user.impersonator_user_id is None
    assert user.is_impersonating is False


@pytest.mark.asyncio
async def test_require_impersonation_allowed_blocks_while_impersonating():
    guard = require_impersonation_allowed()
    user = CurrentUser(
        sub="sub-1",
        actor_user_id=uuid.uuid4(),
        impersonated_user_id=uuid.uuid4(),
    )

    with pytest.raises(ForbiddenError) as exc_info:
        await guard(user=user)

    assert exc_info.value.error_code == "impersonation_restricted"


@pytest.mark.asyncio
async def test_require_impersonation_allowed_passes_when_not_impersonating():
    guard = require_impersonation_allowed()
    user = CurrentUser(sub="sub-1", actor_user_id=uuid.uuid4())

    result = await guard(user=user)
    assert result is user


@pytest.mark.asyncio
async def test_get_current_user_loads_impersonation_session():
    from app.core.auth import get_current_user

    actor = _user(platform_role=PlatformRole.super_admin)
    target = _user(email="target@example.com")
    target.id = uuid.uuid4()
    active_session = ImpersonationSessionORM(
        actor_user_id=actor.id,
        target_user_id=target.id,
        reason="Debugging customer workspace issue",
    )
    workspace_id = uuid.uuid4()
    workspace = WorkspaceORM(slug="acme", name="Acme", status=WorkspaceStatus.active)
    workspace.id = workspace_id
    _ = WorkspaceMembershipORM(
        user_id=target.id,
        workspace_id=workspace_id,
        role=AppRole.viewer,
    )

    session = AsyncMock()
    session.commit = AsyncMock()
    session.refresh = AsyncMock()
    session.get = AsyncMock(side_effect=lambda model, pk: {
        actor.id: actor,
        target.id: target,
        workspace_id: workspace,
    }.get(pk))

    with (
        patch("app.core.auth.decode_access_token", new_callable=AsyncMock) as decode,
        patch("app.core.auth.provision_user_from_keycloak", new_callable=AsyncMock) as provision,
        patch("app.core.auth.get_active_session", new_callable=AsyncMock) as get_session,
        patch("app.core.auth._resolve_active_workspace", new_callable=AsyncMock) as resolve_ws,
    ):
        decode.return_value = {"sub": "kc-actor", "email": actor.email}
        provision.return_value = actor
        get_session.return_value = active_session
        resolve_ws.return_value = (workspace_id, AppRole.viewer)

        credentials = MagicMock()
        credentials.scheme = "Bearer"
        credentials.credentials = "token"

        current = await get_current_user(
            credentials=credentials,
            session=session,
            x_workspace_id=str(workspace_id),
        )

    assert current.actor_user_id == actor.id
    assert current.impersonated_user_id == target.id
    assert current.email == target.email
    assert current.workspace_id == workspace_id
    assert current.role == AppRole.viewer
    assert current.platform_role == PlatformRole.super_admin
