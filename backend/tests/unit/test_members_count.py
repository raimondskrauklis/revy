# backend/tests/unit/test_members_count.py
"""Workspace member count API — W8."""
import uuid
from unittest.mock import AsyncMock

import pytest

from app.services.memberships import count_members


@pytest.mark.asyncio
async def test_count_members_returns_total():
    workspace_id = uuid.uuid4()
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=42)

    total = await count_members(session, workspace_id=workspace_id)

    assert total == 42
