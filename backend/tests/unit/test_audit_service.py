# backend/tests/unit/test_audit_service.py
"""record_audit and list_workspace_audit — AUDIT.md."""
import json
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.constants.enums import UserStatus
from app.core.pagination import CursorParams
from app.models.audit_log import AuditLogORM
from app.models.users import UserORM
from app.services.audit_service import list_workspace_audit, record_audit


@pytest.mark.asyncio
async def test_record_audit_persists_row():
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()

    actor_id = uuid.uuid4()
    workspace_id = uuid.uuid4()

    row = await record_audit(
        session,
        actor_user_id=actor_id,
        workspace_id=workspace_id,
        action="workspace.updated",
        resource_type="workspace",
        resource_id=str(workspace_id),
        metadata={"old_name": "Acme", "new_name": "Acme Corp"},
    )

    session.add.assert_called_once()
    session.flush.assert_awaited_once()
    assert row.action == "workspace.updated"
    assert row.actor_user_id == actor_id
    assert row.workspace_id == workspace_id
    assert row.metadata_json == {"old_name": "Acme", "new_name": "Acme Corp"}


def _audit_row(
    *,
    workspace_id: uuid.UUID,
    actor_id: uuid.UUID,
    action: str = "workspace.updated",
    metadata: dict | None = None,
    impersonator_id: uuid.UUID | None = None,
) -> tuple[AuditLogORM, UserORM, UserORM | None]:
    actor = UserORM(
        keycloak_user_id="kc-1",
        email="actor@example.com",
        full_name="Actor",
        status=UserStatus.active,
    )
    actor.id = actor_id

    impersonator = None
    if impersonator_id is not None:
        impersonator = UserORM(
            keycloak_user_id="kc-admin",
            email="admin@example.com",
            full_name="Admin",
            status=UserStatus.active,
        )
        impersonator.id = impersonator_id

    row = AuditLogORM(
        actor_user_id=actor_id,
        impersonator_user_id=impersonator_id,
        workspace_id=workspace_id,
        action=action,
        resource_type="workspace",
        resource_id=str(workspace_id),
        metadata_json=metadata or {},
    )
    row.id = uuid.uuid4()
    row.created_at = datetime.now(UTC)
    return row, actor, impersonator


@pytest.mark.asyncio
async def test_record_audit_persists_impersonator():
    session = AsyncMock()
    session.add = MagicMock()
    session.flush = AsyncMock()

    actor_id = uuid.uuid4()
    impersonator_id = uuid.uuid4()
    workspace_id = uuid.uuid4()

    row = await record_audit(
        session,
        actor_user_id=actor_id,
        impersonator_user_id=impersonator_id,
        workspace_id=workspace_id,
        action="workspace.updated",
    )

    assert row.impersonator_user_id == impersonator_id


@pytest.mark.asyncio
async def test_list_workspace_audit_returns_joined_rows():
    workspace_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    audit_row, actor, impersonator = _audit_row(workspace_id=workspace_id, actor_id=actor_id)

    session = AsyncMock()
    result = MagicMock()
    result.all.return_value = [(audit_row, actor, impersonator)]
    session.execute = AsyncMock(return_value=result)

    page = await list_workspace_audit(
        session, workspace_id=workspace_id, params=CursorParams(limit=10)
    )

    assert len(page.items) == 1
    assert page.items[0].actor_email == "actor@example.com"
    assert page.items[0].action == "workspace.updated"
    assert page.cursor.has_next is False


@pytest.mark.asyncio
async def test_list_workspace_audit_caps_oversized_metadata():
    workspace_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    large_metadata = {"payload": "x" * 5000}
    audit_row, actor, impersonator = _audit_row(
        workspace_id=workspace_id,
        actor_id=actor_id,
        metadata=large_metadata,
    )

    session = AsyncMock()
    result = MagicMock()
    result.all.return_value = [(audit_row, actor, impersonator)]
    session.execute = AsyncMock(return_value=result)

    page = await list_workspace_audit(
        session, workspace_id=workspace_id, params=CursorParams(limit=10)
    )

    assert page.items[0].metadata == {}


@pytest.mark.asyncio
async def test_list_workspace_audit_pagination_has_next():
    workspace_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    rows = [_audit_row(workspace_id=workspace_id, actor_id=actor_id) for _ in range(3)]

    session = AsyncMock()
    result = MagicMock()
    result.all.return_value = rows
    session.execute = AsyncMock(return_value=result)

    page = await list_workspace_audit(
        session, workspace_id=workspace_id, params=CursorParams(limit=2)
    )

    assert len(page.items) == 2
    assert page.cursor.has_next is True
    assert page.cursor.next_cursor is not None


@pytest.mark.asyncio
async def test_list_workspace_audit_passes_through_small_metadata():
    workspace_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    metadata = {"old_name": "Acme", "new_name": "Acme Corp"}
    audit_row, actor, impersonator = _audit_row(
        workspace_id=workspace_id,
        actor_id=actor_id,
        metadata=metadata,
        impersonator_id=uuid.uuid4(),
    )

    session = AsyncMock()
    result = MagicMock()
    result.all.return_value = [(audit_row, actor, impersonator)]
    session.execute = AsyncMock(return_value=result)

    page = await list_workspace_audit(
        session, workspace_id=workspace_id, params=CursorParams(limit=10)
    )

    assert page.items[0].metadata == metadata
    assert page.items[0].impersonator_email == "admin@example.com"
    assert len(json.dumps(page.items[0].metadata).encode("utf-8")) <= 4096
