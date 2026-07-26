# backend/tests/unit/test_workspaces.py
"""Workspace settings service — TENANCY.md."""
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.constants.enums import WorkspaceStatus
from app.core.exceptions import NotFoundError, ValidationError
from app.models.workspaces import WorkspaceORM
from app.schemas.workspaces import WorkspaceUpdate
from app.services.workspaces import update_workspace


def _workspace(*, review_autostart_enabled: bool = True) -> WorkspaceORM:
    workspace_id = uuid.uuid4()
    workspace = WorkspaceORM(
        slug="acme",
        name="Acme",
        status=WorkspaceStatus.active,
        review_autostart_enabled=review_autostart_enabled,
    )
    workspace.id = workspace_id
    return workspace


@pytest.mark.asyncio
async def test_update_workspace_changes_name():
    workspace = _workspace()
    workspace_id = workspace.id

    session = AsyncMock()
    session.get = AsyncMock(return_value=workspace)
    session.flush = AsyncMock()

    updated = await update_workspace(session, workspace_id=workspace_id, name="  Acme Corp  ")

    assert updated.name == "Acme Corp"
    session.flush.assert_awaited()


@pytest.mark.asyncio
async def test_update_workspace_rejects_empty_name():
    workspace = _workspace()
    workspace_id = workspace.id

    session = AsyncMock()
    session.get = AsyncMock(return_value=workspace)

    with pytest.raises(ValidationError, match="Name is required"):
        await update_workspace(session, workspace_id=workspace_id, name="   ")


@pytest.mark.asyncio
async def test_update_workspace_not_found():
    session = AsyncMock()
    session.get = AsyncMock(return_value=None)

    with pytest.raises(NotFoundError):
        await update_workspace(session, workspace_id=uuid.uuid4(), name="Acme")


@pytest.mark.asyncio
async def test_update_workspace_rejects_empty_patch():
    workspace = _workspace()
    session = AsyncMock()
    session.get = AsyncMock(return_value=workspace)

    with pytest.raises(ValidationError, match="At least one of"):
        await update_workspace(session, workspace_id=workspace.id)


@pytest.mark.asyncio
@patch("app.services.workspaces.record_audit", new_callable=AsyncMock)
async def test_update_workspace_review_autostart_records_audit(mock_audit: AsyncMock):
    workspace = _workspace(review_autostart_enabled=True)
    workspace_id = workspace.id
    actor_id = uuid.uuid4()

    session = AsyncMock()
    session.get = AsyncMock(return_value=workspace)
    session.flush = AsyncMock()

    updated = await update_workspace(
        session,
        workspace_id=workspace_id,
        review_autostart_enabled=False,
        actor_user_id=actor_id,
    )

    assert updated.review_autostart_enabled is False
    mock_audit.assert_awaited_once()
    call_kwargs = mock_audit.await_args.kwargs
    assert call_kwargs["action"] == "workspace.review_autostart_updated"
    assert call_kwargs["metadata"] == {
        "old_review_autostart_enabled": True,
        "new_review_autostart_enabled": False,
    }


@pytest.mark.asyncio
@patch("app.services.workspaces.record_audit", new_callable=AsyncMock)
async def test_update_workspace_review_autostart_skips_audit_when_unchanged(mock_audit: AsyncMock):
    workspace = _workspace(review_autostart_enabled=True)
    session = AsyncMock()
    session.get = AsyncMock(return_value=workspace)
    session.flush = AsyncMock()

    await update_workspace(
        session,
        workspace_id=workspace.id,
        review_autostart_enabled=True,
        actor_user_id=uuid.uuid4(),
    )

    mock_audit.assert_not_awaited()


def test_workspace_update_schema_requires_at_least_one_field():
    with pytest.raises(ValueError, match="At least one of"):
        WorkspaceUpdate()

    assert WorkspaceUpdate(name="Acme").name == "Acme"
    assert WorkspaceUpdate(review_autostart_enabled=False).review_autostart_enabled is False
