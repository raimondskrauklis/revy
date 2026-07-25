# backend/tests/unit/test_admin_workspaces.py
"""Platform admin workspace directory — W5."""
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.constants.enums import WorkspaceStatus
from app.core.auth import _resolve_active_workspace
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.pagination import CursorParams
from app.models.users import UserORM
from app.models.workspaces import WorkspaceORM
from app.services.admin_workspaces import (
    get_workspace_detail,
    list_workspaces,
    suspend_workspace,
    unsuspend_workspace,
)


def _workspace(
    *,
    status: WorkspaceStatus = WorkspaceStatus.active,
    stripe_customer_id: str | None = "cus_abc123",
) -> WorkspaceORM:
    workspace = WorkspaceORM(
        slug="acme",
        name="Acme Corp",
        status=status,
        plan="pro",
        stripe_customer_id=stripe_customer_id,
    )
    workspace.id = uuid.uuid4()
    workspace.created_at = datetime.now(UTC)
    workspace.updated_at = datetime.now(UTC)
    return workspace


@pytest.mark.asyncio
async def test_list_workspaces_returns_items():
    workspace = _workspace()
    session = AsyncMock()
    result = MagicMock()
    result.all.return_value = [(workspace, 3)]
    session.execute = AsyncMock(return_value=result)

    page = await list_workspaces(session, params=CursorParams(limit=10))

    assert len(page.items) == 1
    assert page.items[0].name == "Acme Corp"
    assert page.items[0].member_count == 3
    assert page.cursor.has_next is False


@pytest.mark.asyncio
async def test_get_workspace_detail_masks_stripe_customer():
    workspace = _workspace()
    actor_id = uuid.uuid4()
    session = AsyncMock()
    session.get = AsyncMock(return_value=workspace)
    session.scalar = AsyncMock(return_value=2)

    with patch("app.services.admin_workspaces.record_audit", new_callable=AsyncMock) as record:
        detail = await get_workspace_detail(
            session,
            workspace_id=workspace.id,
            actor_user_id=actor_id,
        )

    assert detail.stripe_customer_id == "cus_***"
    assert detail.member_count == 2
    record.assert_awaited_once()
    assert record.await_args.kwargs["action"] == "platform.workspace.viewed"


@pytest.mark.asyncio
async def test_get_workspace_detail_not_found():
    session = AsyncMock()
    session.get = AsyncMock(return_value=None)

    with pytest.raises(NotFoundError):
        await get_workspace_detail(
            session,
            workspace_id=uuid.uuid4(),
            actor_user_id=uuid.uuid4(),
        )


@pytest.mark.asyncio
async def test_suspend_workspace_sets_status():
    workspace = _workspace()
    actor_id = uuid.uuid4()
    session = AsyncMock()
    session.get = AsyncMock(return_value=workspace)
    session.flush = AsyncMock()
    session.scalar = AsyncMock(return_value=1)

    with patch("app.services.admin_workspaces.record_audit", new_callable=AsyncMock) as record:
        detail = await suspend_workspace(
            session,
            workspace_id=workspace.id,
            actor_user_id=actor_id,
        )

    assert workspace.status == WorkspaceStatus.suspended
    assert detail.status == WorkspaceStatus.suspended
    record.assert_awaited_once()
    assert record.await_args.kwargs["action"] == "platform.workspace.suspended"


@pytest.mark.asyncio
async def test_unsuspend_workspace_sets_active():
    workspace = _workspace(status=WorkspaceStatus.suspended)
    actor_id = uuid.uuid4()
    session = AsyncMock()
    session.get = AsyncMock(return_value=workspace)
    session.flush = AsyncMock()
    session.scalar = AsyncMock(return_value=1)

    with patch("app.services.admin_workspaces.record_audit", new_callable=AsyncMock) as record:
        detail = await unsuspend_workspace(
            session,
            workspace_id=workspace.id,
            actor_user_id=actor_id,
        )

    assert workspace.status == WorkspaceStatus.active
    assert detail.status == WorkspaceStatus.active
    record.assert_awaited_once()
    assert record.await_args.kwargs["action"] == "platform.workspace.unsuspended"


@pytest.mark.asyncio
async def test_resolve_active_workspace_rejects_suspended():
    from app.constants.enums import AppRole, UserStatus
    from app.models.workspace_memberships import WorkspaceMembershipORM

    user = UserORM(
        keycloak_user_id="kc-1",
        email="member@example.com",
        status=UserStatus.active,
    )
    user.id = uuid.uuid4()
    workspace = _workspace(status=WorkspaceStatus.suspended)
    membership = WorkspaceMembershipORM(
        user_id=user.id,
        workspace_id=workspace.id,
        role=AppRole.admin,
    )

    session = AsyncMock()
    scalars_result = MagicMock()
    scalars_result.all.return_value = [membership]
    session.scalars = AsyncMock(return_value=scalars_result)
    session.get = AsyncMock(return_value=workspace)

    with pytest.raises(ForbiddenError) as exc_info:
        await _resolve_active_workspace(
            session,
            user,
            header_workspace_id=str(workspace.id),
        )

    assert exc_info.value.error_code == "workspace_suspended"
