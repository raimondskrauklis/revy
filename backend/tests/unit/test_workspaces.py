# backend/tests/unit/test_workspaces.py
"""Workspace settings service — TENANCY.md."""
import uuid
from unittest.mock import AsyncMock

import pytest

from app.constants.enums import WorkspaceStatus
from app.core.exceptions import NotFoundError, ValidationError
from app.models.workspaces import WorkspaceORM
from app.services.workspaces import update_workspace


@pytest.mark.asyncio
async def test_update_workspace_changes_name():
    workspace_id = uuid.uuid4()
    workspace = WorkspaceORM(
        slug="acme",
        name="Acme",
        status=WorkspaceStatus.active,
    )
    workspace.id = workspace_id

    session = AsyncMock()
    session.get = AsyncMock(return_value=workspace)
    session.flush = AsyncMock()

    updated = await update_workspace(session, workspace_id=workspace_id, name="  Acme Corp  ")

    assert updated.name == "Acme Corp"
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_update_workspace_rejects_empty_name():
    workspace_id = uuid.uuid4()
    workspace = WorkspaceORM(
        slug="acme",
        name="Acme",
        status=WorkspaceStatus.active,
    )
    workspace.id = workspace_id

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
