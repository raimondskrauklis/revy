# backend/tests/unit/test_github_repository_routes.py
"""Installation repository routes — R1."""
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.api.v1.workspaces.installation_repositories import (
    get_installation_repositories,
    post_sync_installation_repositories,
)
from app.core.exceptions import ServiceUnavailableError
from app.core.pagination import CursorMeta, CursorParams, CursorResponse


@pytest.mark.asyncio
async def test_get_installation_repositories_returns_page():
    workspace_id = uuid.uuid4()
    installation_id = uuid.uuid4()
    session = AsyncMock()
    current_user = AsyncMock()
    current_user.workspace_id = workspace_id

    page = CursorResponse(
        items=[],
        cursor=CursorMeta(next_cursor=None, has_next=False),
    )

    with patch(
        "app.api.v1.workspaces.installation_repositories.require_permission",
    ):
        with patch(
            "app.api.v1.workspaces.installation_repositories.require_same_workspace",
        ):
            with patch(
                "app.api.v1.workspaces.installation_repositories.list_github_repositories",
                AsyncMock(return_value=page),
            ):
                response = await get_installation_repositories(
                    workspace_id=workspace_id,
                    installation_id=installation_id,
                    current_user=current_user,
                    session=session,
                    params=CursorParams(limit=50),
                )

    assert response.data.items == []


@pytest.mark.asyncio
async def test_post_sync_installation_repositories_disabled_raises():
    workspace_id = uuid.uuid4()
    installation_id = uuid.uuid4()
    session = AsyncMock()
    current_user = AsyncMock()
    current_user.workspace_id = workspace_id
    current_user.user_id = uuid.uuid4()

    with patch(
        "app.api.v1.workspaces.installation_repositories.require_permission",
    ):
        with patch(
            "app.api.v1.workspaces.installation_repositories.require_same_workspace",
        ):
            with patch(
                "app.api.v1.workspaces.installation_repositories.settings"
            ) as mock_settings:
                mock_settings.github_api_enabled = False
                with pytest.raises(ServiceUnavailableError) as exc:
                    await post_sync_installation_repositories(
                        workspace_id=workspace_id,
                        installation_id=installation_id,
                        current_user=current_user,
                        session=session,
                        idempotent=None,
                    )

    assert exc.value.error_code == "github_api_disabled"


@pytest.mark.asyncio
async def test_post_sync_installation_repositories_queues_task():
    workspace_id = uuid.uuid4()
    installation_id = uuid.uuid4()
    session = AsyncMock()
    session.commit = AsyncMock()
    current_user = AsyncMock()
    current_user.workspace_id = workspace_id
    current_user.user_id = uuid.uuid4()

    with patch(
        "app.api.v1.workspaces.installation_repositories.require_permission",
    ):
        with patch(
            "app.api.v1.workspaces.installation_repositories.require_same_workspace",
        ):
            with patch(
                "app.api.v1.workspaces.installation_repositories.settings"
            ) as mock_settings:
                mock_settings.github_api_enabled = True
                with patch(
                    "app.services.github_installations.get_github_installation",
                    AsyncMock(),
                ):
                    with patch(
                        "app.api.v1.workspaces.installation_repositories.enqueue_installation_repository_sync",
                    ) as enqueue_mock:
                        response = await post_sync_installation_repositories(
                            workspace_id=workspace_id,
                            installation_id=installation_id,
                            current_user=current_user,
                            session=session,
                            idempotent=None,
                        )

    enqueue_mock.assert_called_once_with(installation_id)
    assert response.data["status"] == "queued"
