# backend/tests/unit/test_account_lifecycle.py
"""Account lifecycle service — ACCOUNT_LIFECYCLE.md."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.constants.enums import AppRole, PlatformRole, UserStatus, WorkspaceStatus
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.models.users import UserORM
from app.models.workspace_memberships import WorkspaceMembershipORM
from app.models.workspaces import WorkspaceORM
from app.services.account_lifecycle import delete_account, delete_workspace, leave_workspace


def _membership(*, workspace_id: uuid.UUID, user_id: uuid.UUID, role: AppRole) -> WorkspaceMembershipORM:
    membership = WorkspaceMembershipORM(
        user_id=user_id,
        workspace_id=workspace_id,
        role=role,
    )
    return membership


@pytest.mark.asyncio
async def test_leave_workspace_records_audit():
    workspace_id = uuid.uuid4()
    user_id = uuid.uuid4()
    membership = _membership(workspace_id=workspace_id, user_id=user_id, role=AppRole.viewer)

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=membership)
    session.delete = AsyncMock()
    session.flush = AsyncMock()

    with patch("app.services.account_lifecycle.record_audit", new_callable=AsyncMock) as record:
        await leave_workspace(session, workspace_id=workspace_id, user_id=user_id)

    session.delete.assert_awaited_once_with(membership)
    record.assert_awaited_once()
    assert record.await_args.kwargs["action"] == "workspace.left"


@pytest.mark.asyncio
async def test_leave_workspace_blocks_last_admin():
    workspace_id = uuid.uuid4()
    user_id = uuid.uuid4()
    membership = _membership(workspace_id=workspace_id, user_id=user_id, role=AppRole.admin)

    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[membership, MagicMock(), 1])
    session.delete = AsyncMock()
    session.flush = AsyncMock()

    with pytest.raises(ForbiddenError) as exc_info:
        await leave_workspace(session, workspace_id=workspace_id, user_id=user_id)

    assert exc_info.value.error_code == "last_workspace_admin"
    session.delete.assert_not_called()


@pytest.mark.asyncio
async def test_delete_workspace_requires_slug_confirmation():
    workspace_id = uuid.uuid4()
    workspace = WorkspaceORM(slug="acme", name="Acme", status=WorkspaceStatus.active)
    workspace.id = workspace_id

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=workspace)
    session.execute = AsyncMock()
    session.flush = AsyncMock()

    with pytest.raises(ValidationError) as exc_info:
        await delete_workspace(
            session,
            workspace_id=workspace_id,
            confirm_slug="wrong",
            actor_user_id=uuid.uuid4(),
        )

    assert exc_info.value.field == "confirm_slug"


@pytest.mark.asyncio
async def test_delete_workspace_blocks_active_subscription():
    workspace_id = uuid.uuid4()
    workspace = WorkspaceORM(
        slug="acme",
        name="Acme",
        status=WorkspaceStatus.active,
        plan="pro",
        stripe_customer_id="cus_123",
    )
    workspace.id = workspace_id

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=workspace)

    with pytest.raises(ForbiddenError) as exc_info:
        await delete_workspace(
            session,
            workspace_id=workspace_id,
            confirm_slug="acme",
            actor_user_id=uuid.uuid4(),
        )

    assert exc_info.value.error_code == "subscription_active"


@pytest.mark.asyncio
async def test_delete_workspace_soft_deletes_and_audits():
    workspace_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    workspace = WorkspaceORM(slug="acme", name="Acme", status=WorkspaceStatus.active)
    workspace.id = workspace_id

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=workspace)
    session.execute = AsyncMock()
    session.flush = AsyncMock()

    with patch("app.services.account_lifecycle.record_audit", new_callable=AsyncMock) as record:
        await delete_workspace(
            session,
            workspace_id=workspace_id,
            confirm_slug="acme",
            actor_user_id=actor_id,
        )

    assert workspace.status == WorkspaceStatus.deleted
    session.execute.assert_awaited_once()
    record.assert_awaited_once()
    assert record.await_args.kwargs["action"] == "workspace.deleted"


@pytest.mark.asyncio
async def test_delete_account_requires_email_confirmation():
    user_id = uuid.uuid4()
    user = UserORM(
        keycloak_user_id="kc-1",
        email="user@example.com",
        status=UserStatus.active,
    )
    user.id = user_id

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=user)

    with pytest.raises(ValidationError) as exc_info:
        await delete_account(session, user_id=user_id, confirm_email="other@example.com")

    assert exc_info.value.field == "confirm_email"


@pytest.mark.asyncio
async def test_delete_account_blocks_platform_admin():
    user_id = uuid.uuid4()
    user = UserORM(
        keycloak_user_id="kc-1",
        email="admin@example.com",
        status=UserStatus.active,
        platform_role=PlatformRole.super_admin,
    )
    user.id = user_id

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=user)

    with pytest.raises(ForbiddenError) as exc_info:
        await delete_account(session, user_id=user_id, confirm_email="admin@example.com")

    assert exc_info.value.error_code == "platform_admin_protected"


@pytest.mark.asyncio
async def test_delete_account_blocks_sole_workspace_admin():
    user_id = uuid.uuid4()
    workspace_id = uuid.uuid4()
    user = UserORM(
        keycloak_user_id="kc-1",
        email="user@example.com",
        status=UserStatus.active,
    )
    user.id = user_id
    membership = _membership(workspace_id=workspace_id, user_id=user_id, role=AppRole.admin)

    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[user, 1])
    session.scalars = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=[membership])))

    with pytest.raises(ForbiddenError) as exc_info:
        await delete_account(session, user_id=user_id, confirm_email="user@example.com")

    assert exc_info.value.error_code == "sole_workspace_admin"


@pytest.mark.asyncio
async def test_delete_account_anonymizes_and_audits():
    user_id = uuid.uuid4()
    user = UserORM(
        keycloak_user_id="kc-1",
        email="user@example.com",
        full_name="User",
        status=UserStatus.active,
    )
    user.id = user_id

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=user)
    session.scalars = AsyncMock(return_value=MagicMock(all=MagicMock(return_value=[])))
    session.execute = AsyncMock()
    session.flush = AsyncMock()

    with patch("app.services.account_lifecycle.record_audit", new_callable=AsyncMock) as record:
        await delete_account(session, user_id=user_id, confirm_email="user@example.com")

    assert user.status == UserStatus.deleted
    assert user.email == f"deleted+{user_id}@revy.invalid"
    assert user.full_name is None
    record.assert_awaited_once()
    assert record.await_args.kwargs["action"] == "user.deleted"


@pytest.mark.asyncio
async def test_leave_workspace_not_found():
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)

    with pytest.raises(NotFoundError):
        await leave_workspace(session, workspace_id=uuid.uuid4(), user_id=uuid.uuid4())
