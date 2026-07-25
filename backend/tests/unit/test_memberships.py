# backend/tests/unit/test_memberships.py
"""Workspace membership service — TENANCY.md."""
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.constants.enums import AppRole, UserStatus
from app.core.exceptions import ForbiddenError, NotFoundError
from app.core.pagination import CursorParams
from app.models.users import UserORM
from app.models.workspace_memberships import WorkspaceMembershipORM
from app.services.memberships import list_members, remove_member, update_member_role


def _membership(
    *,
    workspace_id: uuid.UUID,
    user_id: uuid.UUID,
    role: AppRole,
) -> WorkspaceMembershipORM:
    membership = WorkspaceMembershipORM(
        user_id=user_id,
        workspace_id=workspace_id,
        role=role,
    )
    membership.created_at = datetime.now(UTC)
    return membership


@pytest.mark.asyncio
async def test_list_members_returns_joined_rows():
    workspace_id = uuid.uuid4()
    user_id = uuid.uuid4()
    user = UserORM(
        keycloak_user_id="kc-1",
        email="member@example.com",
        full_name="Member",
        status=UserStatus.active,
    )
    user.id = user_id
    membership = _membership(workspace_id=workspace_id, user_id=user_id, role=AppRole.viewer)

    session = AsyncMock()
    result = MagicMock()
    result.all.return_value = [(membership, user)]
    session.execute = AsyncMock(return_value=result)

    page = await list_members(session, workspace_id=workspace_id, params=CursorParams(limit=50))

    assert len(page.items) == 1
    assert page.items[0].email == "member@example.com"
    assert page.items[0].role == AppRole.viewer


@pytest.mark.asyncio
async def test_update_member_role_demotes_viewer():
    workspace_id = uuid.uuid4()
    user_id = uuid.uuid4()
    membership = _membership(workspace_id=workspace_id, user_id=user_id, role=AppRole.viewer)

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=membership)
    session.flush = AsyncMock()

    updated = await update_member_role(
        session,
        workspace_id=workspace_id,
        user_id=user_id,
        role=AppRole.operator,
    )

    assert updated.role == AppRole.operator


@pytest.mark.asyncio
async def test_update_member_role_records_impersonator_in_audit():
    workspace_id = uuid.uuid4()
    user_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    impersonator_id = uuid.uuid4()
    membership = _membership(workspace_id=workspace_id, user_id=user_id, role=AppRole.viewer)

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=membership)
    session.flush = AsyncMock()

    with patch("app.services.memberships.record_audit", AsyncMock()) as record_audit:
        await update_member_role(
            session,
            workspace_id=workspace_id,
            user_id=user_id,
            role=AppRole.operator,
            actor_user_id=actor_id,
            impersonator_user_id=impersonator_id,
        )

    record_audit.assert_awaited_once()
    assert record_audit.await_args.kwargs["actor_user_id"] == actor_id
    assert record_audit.await_args.kwargs["impersonator_user_id"] == impersonator_id


@pytest.mark.asyncio
async def test_update_member_role_blocks_last_admin_demotion():
    workspace_id = uuid.uuid4()
    user_id = uuid.uuid4()
    membership = _membership(workspace_id=workspace_id, user_id=user_id, role=AppRole.admin)

    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[membership, MagicMock(), 1])
    session.flush = AsyncMock()

    with pytest.raises(ForbiddenError) as exc_info:
        await update_member_role(
            session,
            workspace_id=workspace_id,
            user_id=user_id,
            role=AppRole.viewer,
        )

    assert exc_info.value.error_code == "last_workspace_admin"


@pytest.mark.asyncio
async def test_remove_member_blocks_last_admin():
    workspace_id = uuid.uuid4()
    user_id = uuid.uuid4()
    membership = _membership(workspace_id=workspace_id, user_id=user_id, role=AppRole.admin)

    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[membership, MagicMock(), 1])
    session.delete = AsyncMock()
    session.flush = AsyncMock()

    with pytest.raises(ForbiddenError) as exc_info:
        await remove_member(session, workspace_id=workspace_id, user_id=user_id)

    assert exc_info.value.error_code == "last_workspace_admin"
    session.delete.assert_not_called()


@pytest.mark.asyncio
async def test_remove_member_deletes_row():
    workspace_id = uuid.uuid4()
    user_id = uuid.uuid4()
    membership = _membership(workspace_id=workspace_id, user_id=user_id, role=AppRole.viewer)

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=membership)
    session.delete = AsyncMock()
    session.flush = AsyncMock()

    await remove_member(session, workspace_id=workspace_id, user_id=user_id)

    session.delete.assert_called_once_with(membership)


@pytest.mark.asyncio
async def test_remove_member_not_found():
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)

    with pytest.raises(NotFoundError):
        await remove_member(session, workspace_id=uuid.uuid4(), user_id=uuid.uuid4())
