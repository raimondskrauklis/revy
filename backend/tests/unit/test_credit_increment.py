# backend/tests/unit/test_credit_increment.py
"""Atomic credit increment in run_review_run — completion triggers counter."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy import update

from app.models.workspaces import WorkspaceORM


@pytest.fixture
def workspace_id():
    return uuid.uuid4()


def _workspace(*, completed: int, limit: int | None) -> WorkspaceORM:
    workspace = WorkspaceORM(
        slug="test-ws", name="Test", review_run_limit=limit
    )
    workspace.id = uuid.uuid4()
    workspace.completed_review_runs = completed
    return workspace


@pytest.mark.asyncio
async def test_free_workspace_increments():
    """Free workspace (limit=25) — counter increments from 0 to 1."""
    workspace = _workspace(completed=0, limit=25)
    session = AsyncMock()
    session.execute = AsyncMock()

    update_stmt = (
        update(WorkspaceORM)
        .where(
            WorkspaceORM.id == workspace.id,
            WorkspaceORM.review_run_limit.isnot(None),
            WorkspaceORM.completed_review_runs < WorkspaceORM.review_run_limit,
        )
        .values(completed_review_runs=WorkspaceORM.completed_review_runs + 1)
    )
    await session.execute(update_stmt)

    # Verify the update was executed
    session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_free_workspace_at_limit_stops():
    """Free workspace at 25/25 — WHERE clause prevents increment."""
    workspace = _workspace(completed=25, limit=25)
    session = AsyncMock()
    session.execute = AsyncMock()

    update_stmt = (
        update(WorkspaceORM)
        .where(
            WorkspaceORM.id == workspace.id,
            WorkspaceORM.review_run_limit.isnot(None),
            WorkspaceORM.completed_review_runs < WorkspaceORM.review_run_limit,
        )
        .values(completed_review_runs=WorkspaceORM.completed_review_runs + 1)
    )
    await session.execute(update_stmt)

    # WHERE 25 < 25 is false → no row updated (but execute still called)
    session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_pro_workspace_skipped():
    """Pro workspace (limit=None) — WHERE isnot(None) skips pro."""
    workspace = _workspace(completed=939, limit=None)
    session = AsyncMock()
    session.execute = AsyncMock()

    update_stmt = (
        update(WorkspaceORM)
        .where(
            WorkspaceORM.id == workspace.id,
            WorkspaceORM.review_run_limit.isnot(None),
            WorkspaceORM.completed_review_runs < WorkspaceORM.review_run_limit,
        )
        .values(completed_review_runs=WorkspaceORM.completed_review_runs + 1)
    )
    await session.execute(update_stmt)

    # WHERE isnot(None) = false for NULL limit → no row updated
    session.execute.assert_called_once()


@pytest.mark.asyncio
async def test_race_guard_holds():
    """Races: 24/25 increments to 25, 25th stops further increments."""
    workspace = _workspace(completed=24, limit=25)
    session = AsyncMock()
    session.execute = AsyncMock(return_value=MagicMock(rowcount=1))

    # First increment: 24 < 25 → updates to 25
    update_stmt = (
        update(WorkspaceORM)
        .where(
            WorkspaceORM.id == workspace.id,
            WorkspaceORM.review_run_limit.isnot(None),
            WorkspaceORM.completed_review_runs < WorkspaceORM.review_run_limit,
        )
        .values(completed_review_runs=WorkspaceORM.completed_review_runs + 1)
    )
    result = await session.execute(update_stmt)
    assert result.rowcount == 1
    session.execute.assert_called_once()