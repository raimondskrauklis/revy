# backend/tests/unit/test_github_pull_request_routes.py
"""Repository pull request routes — R2."""
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.api.v1.workspaces.installation_pull_requests import get_repository_pull_requests
from app.core.pagination import CursorMeta, CursorParams, CursorResponse


@pytest.mark.asyncio
async def test_get_repository_pull_requests_returns_page():
    workspace_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    session = AsyncMock()
    current_user = AsyncMock()
    current_user.workspace_id = workspace_id

    page = CursorResponse(
        items=[],
        cursor=CursorMeta(next_cursor=None, has_next=False),
    )

    with patch(
        "app.api.v1.workspaces.installation_pull_requests.require_permission",
    ):
        with patch(
            "app.api.v1.workspaces.installation_pull_requests.require_same_workspace",
        ):
            with patch(
                "app.api.v1.workspaces.installation_pull_requests.list_github_pull_requests",
                AsyncMock(return_value=page),
            ):
                response = await get_repository_pull_requests(
                    workspace_id=workspace_id,
                    repository_id=repository_id,
                    current_user=current_user,
                    session=session,
                    params=CursorParams(limit=50),
                )

    assert response.data.items == []
