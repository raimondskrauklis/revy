# backend/tests/unit/test_impersonation_service.py
"""Impersonation service — W7."""
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.constants.enums import AppRole, PlatformRole, UserStatus, WorkspaceStatus
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.core.pagination import CursorParams
from app.models.impersonation_session import ImpersonationSessionORM
from app.models.users import UserORM
from app.models.workspace_memberships import WorkspaceMembershipORM
from app.models.workspaces import WorkspaceORM
from app.services.impersonation import (
    get_active_impersonation_status,
    list_workspace_members_for_admin,
    start_impersonation,
    stop_impersonation,
)


def _user(
    *,
    status: UserStatus = UserStatus.active,
    platform_role: PlatformRole | None = None,
    email: str = "user@example.com",
) -> UserORM:
    user = UserORM(
        keycloak_user_id=f"kc-{uuid.uuid4()}",
        email=email,
        status=status,
        platform_role=platform_role,
    )
    user.id = uuid.uuid4()
    return user


@pytest.mark.asyncio
async def test_start_impersonation_creates_session():
    actor_id = uuid.uuid4()
    target = _user(email="target@example.com")
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)
    session.get = AsyncMock(return_value=target)
    session.add = MagicMock()
    session.flush = AsyncMock()

    with patch("app.services.impersonation.record_audit", new_callable=AsyncMock) as record:
        status = await start_impersonation(
            session,
            actor_user_id=actor_id,
            target_user_id=target.id,
            reason="Support ticket #999 — login issue",
        )

    assert status.active is True
    assert status.target_user_id == target.id
    assert status.target_email == "target@example.com"
    session.add.assert_called_once()
    record.assert_awaited_once()
    assert record.await_args.kwargs["action"] == "platform.impersonation.started"


@pytest.mark.asyncio
async def test_start_impersonation_rejects_active_session():
    actor_id = uuid.uuid4()
    existing = ImpersonationSessionORM(
        actor_user_id=actor_id,
        target_user_id=uuid.uuid4(),
        reason="Existing session reason text",
    )
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=existing)

    with pytest.raises(ConflictError) as exc_info:
        await start_impersonation(
            session,
            actor_user_id=actor_id,
            target_user_id=uuid.uuid4(),
            reason="Another support investigation",
        )

    assert exc_info.value.error_code == "impersonation_active"


@pytest.mark.asyncio
async def test_start_impersonation_rejects_super_admin_target():
    actor_id = uuid.uuid4()
    target = _user(platform_role=PlatformRole.super_admin)
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)
    session.get = AsyncMock(return_value=target)

    with pytest.raises(ForbiddenError) as exc_info:
        await start_impersonation(
            session,
            actor_user_id=actor_id,
            target_user_id=target.id,
            reason="Attempting to impersonate admin",
        )

    assert exc_info.value.error_code == "impersonation_forbidden"


@pytest.mark.asyncio
async def test_start_impersonation_rejects_short_reason():
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)

    with pytest.raises(ValidationError):
        await start_impersonation(
            session,
            actor_user_id=uuid.uuid4(),
            target_user_id=uuid.uuid4(),
            reason="short",
        )


@pytest.mark.asyncio
async def test_stop_impersonation_ends_session():
    actor_id = uuid.uuid4()
    active = ImpersonationSessionORM(
        actor_user_id=actor_id,
        target_user_id=uuid.uuid4(),
        reason="Support ticket #123 — workspace access",
    )
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=active)
    session.flush = AsyncMock()

    with patch("app.services.impersonation.record_audit", new_callable=AsyncMock) as record:
        status = await stop_impersonation(session, actor_user_id=actor_id)

    assert status.active is False
    assert active.ended_at is not None
    record.assert_awaited_once()
    assert record.await_args.kwargs["action"] == "platform.impersonation.stopped"


@pytest.mark.asyncio
async def test_stop_impersonation_not_active():
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)

    with pytest.raises(NotFoundError) as exc_info:
        await stop_impersonation(session, actor_user_id=uuid.uuid4())

    assert exc_info.value.error_code == "impersonation_not_active"


@pytest.mark.asyncio
async def test_get_active_impersonation_status_inactive():
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)

    status = await get_active_impersonation_status(session, actor_user_id=uuid.uuid4())
    assert status.active is False


@pytest.mark.asyncio
async def test_list_workspace_members_for_admin():
    workspace_id = uuid.uuid4()
    workspace = WorkspaceORM(slug="acme", name="Acme", status=WorkspaceStatus.active)
    workspace.id = workspace_id
    user = _user(email="member@example.com")
    membership = WorkspaceMembershipORM(
        user_id=user.id,
        workspace_id=workspace_id,
        role=AppRole.admin,
    )
    membership.id = uuid.uuid4()
    membership.created_at = datetime.now(UTC)

    session = AsyncMock()
    session.get = AsyncMock(return_value=workspace)
    result = MagicMock()
    result.all.return_value = [(membership, user)]
    session.execute = AsyncMock(return_value=result)

    page = await list_workspace_members_for_admin(
        session,
        workspace_id=workspace_id,
        params=CursorParams(limit=10),
    )

    assert len(page.items) == 1
    assert page.items[0].email == "member@example.com"
    assert page.items[0].role == AppRole.admin


@pytest.mark.asyncio
async def test_list_workspace_members_workspace_not_found():
    session = AsyncMock()
    session.get = AsyncMock(return_value=None)

    with pytest.raises(NotFoundError):
        await list_workspace_members_for_admin(
            session,
            workspace_id=uuid.uuid4(),
            params=CursorParams(limit=10),
        )
