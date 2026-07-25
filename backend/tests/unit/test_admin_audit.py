# backend/tests/unit/test_admin_audit.py
"""Platform audit search — W5."""
import uuid
from datetime import UTC, date, datetime
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.constants.enums import UserStatus
from app.core.pagination import CursorParams
from app.models.audit_log import AuditLogORM
from app.models.users import UserORM
from app.services.audit_service import PlatformAuditFilters, list_platform_audit


def _audit_row(
    *,
    workspace_id: uuid.UUID | None,
    actor_id: uuid.UUID,
    action: str = "workspace.updated",
) -> tuple[AuditLogORM, UserORM]:
    actor = UserORM(
        keycloak_user_id="kc-1",
        email="actor@example.com",
        full_name="Actor",
        status=UserStatus.active,
    )
    actor.id = actor_id

    row = AuditLogORM(
        actor_user_id=actor_id,
        workspace_id=workspace_id,
        action=action,
        resource_type="workspace",
        resource_id=str(workspace_id) if workspace_id else None,
        metadata_json={},
    )
    row.id = uuid.uuid4()
    row.created_at = datetime.now(UTC)
    return row, actor


@pytest.mark.asyncio
async def test_list_platform_audit_returns_workspace_id():
    workspace_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    audit_row, actor = _audit_row(workspace_id=workspace_id, actor_id=actor_id)

    session = AsyncMock()
    result = MagicMock()
    result.all.return_value = [(audit_row, actor, None)]
    session.execute = AsyncMock(return_value=result)

    page = await list_platform_audit(session, params=CursorParams(limit=10))

    assert len(page.items) == 1
    assert page.items[0].workspace_id == workspace_id
    assert page.items[0].actor_email == "actor@example.com"


@pytest.mark.asyncio
async def test_list_platform_audit_applies_filters():
    workspace_id = uuid.uuid4()
    actor_id = uuid.uuid4()
    audit_row, actor = _audit_row(
        workspace_id=workspace_id,
        actor_id=actor_id,
        action="platform.workspace.viewed",
    )

    session = AsyncMock()
    result = MagicMock()
    result.all.return_value = [(audit_row, actor, None)]
    session.execute = AsyncMock(return_value=result)

    page = await list_platform_audit(
        session,
        params=CursorParams(limit=10),
        filters=PlatformAuditFilters(
            workspace_id=workspace_id,
            actor_user_id=actor_id,
            action_prefix="platform.",
            created_at_from=date(2026, 1, 1),
            created_at_to=date(2026, 12, 31),
        ),
    )

    assert len(page.items) == 1
    assert page.items[0].action == "platform.workspace.viewed"
    session.execute.assert_awaited_once()
