# backend/tests/unit/test_admin_kpis.py
"""Platform admin KPI aggregates — W5."""
from unittest.mock import AsyncMock

import pytest

from app.services.admin_kpis import get_admin_kpis


@pytest.mark.asyncio
async def test_get_admin_kpis_returns_counts():
    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[10, 8, 2, 50, 3])

    kpis = await get_admin_kpis(session)

    assert kpis.workspaces_total == 10
    assert kpis.workspaces_active == 8
    assert kpis.workspaces_suspended == 2
    assert kpis.users_active == 50
    assert kpis.users_pending_approval == 3
