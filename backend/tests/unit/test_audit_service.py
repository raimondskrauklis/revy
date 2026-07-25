# backend/tests/unit/test_audit_service.py
"""record_audit service — AUDIT.md."""
import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.services.audit_service import record_audit


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
