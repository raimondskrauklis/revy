# backend/tests/unit/test_onboarding_credit_default.py
"""New workspace gets review_run_limit = 25."""
from __future__ import annotations

from unittest.mock import AsyncMock

import pytest

from app.constants.enums import UserStatus
from app.models.users import UserORM
from app.models.workspaces import WorkspaceORM
from app.services.onboarding import activate_user_with_workspace


@pytest.fixture
def mock_session():
    session = AsyncMock()
    session.flush = AsyncMock()
    return session


@pytest.fixture
def mock_user():
    return UserORM(
        id="00000000-0000-0000-0000-000000000001",
        email="test@example.com",
        status=UserStatus.pending_profile,
    )


@pytest.mark.asyncio
async def test_new_workspace_has_review_run_limit(mock_session, mock_user):
    workspace = await activate_user_with_workspace(
        mock_session,
        mock_user,
        name="Test Workspace",
    )

    assert workspace is not None
    assert mock_session.add.called

    # Verify the added workspace has review_run_limit = 25
    add_calls = mock_session.add.call_args_list
    assert len(add_calls) >= 2  # workspace + membership

    workspace_call = add_calls[0][0][0]
    assert isinstance(workspace_call, WorkspaceORM)
    assert workspace_call.review_run_limit == 25


@pytest.mark.asyncio
async def test_new_workspace_review_run_limit_integration(mock_session, mock_user):
    workspace = await activate_user_with_workspace(
        mock_session,
        mock_user,
        name="Integration Test",
    )

    # The returned workspace has review_run_limit set
    assert workspace.review_run_limit == 25

    # Flush was called twice (workspace + membership)
    assert mock_session.flush.call_count == 2