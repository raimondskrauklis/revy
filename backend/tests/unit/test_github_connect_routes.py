# backend/tests/unit/test_github_connect_routes.py
"""Start-connect JWT API — github-onboarding P2."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import parse_qs, urlparse

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.workspaces.installations import (
    post_workspace_installation_connect,
    post_workspace_installation_verify,
    router,
)
from app.constants.enums import AppRole, UserStatus, WorkspaceStatus
from app.core.auth import CurrentUser, get_current_user
from app.core.database import get_db
from app.core.exception_handlers import register_exception_handlers
from app.core.exceptions import ForbiddenError, ServiceUnavailableError
from app.models.workspaces import WorkspaceORM


def _admin(workspace_id: uuid.UUID) -> CurrentUser:
    return CurrentUser(
        sub="kc-admin",
        actor_user_id=uuid.uuid4(),
        email="admin@example.com",
        workspace_id=workspace_id,
        role=AppRole.admin,
        status=UserStatus.active,
    )


def _viewer(workspace_id: uuid.UUID) -> CurrentUser:
    return CurrentUser(
        sub="kc-viewer",
        actor_user_id=uuid.uuid4(),
        email="viewer@example.com",
        workspace_id=workspace_id,
        role=AppRole.viewer,
        status=UserStatus.active,
    )


def _settings(**overrides):
    values = {
        "github_app_slug": "revy",
        "github_client_id": "Iv1.client",
        "github_client_secret": "github-client-secret",
        "github_install_state_ttl_seconds": 1800,
    }
    values.update(overrides)
    return (
        patch("app.api.v1.workspaces.installations.settings", **values),
        patch("app.services.github_install_state.settings", **values),
    )


@pytest.mark.asyncio
async def test_connect_returns_install_url_with_slug_and_state():
    workspace_id = uuid.uuid4()
    route_settings, state_settings = _settings()
    with route_settings, state_settings:
        response = await post_workspace_installation_connect(
            workspace_id=workspace_id,
            current_user=_admin(workspace_id),
        )

    parsed = urlparse(response.data.install_url)
    assert parsed.scheme == "https"
    assert parsed.netloc == "github.com"
    assert parsed.path == "/apps/revy/installations/new"
    assert parse_qs(parsed.query)["state"][0]


@pytest.mark.asyncio
async def test_connect_forbids_non_admin():
    workspace_id = uuid.uuid4()
    with pytest.raises(ForbiddenError) as exc:
        await post_workspace_installation_connect(
            workspace_id=workspace_id,
            current_user=_viewer(workspace_id),
        )
    assert exc.value.error_code == "forbidden"


@pytest.mark.asyncio
async def test_connect_unavailable_when_slug_missing():
    workspace_id = uuid.uuid4()
    route_settings, state_settings = _settings(github_app_slug="")
    with route_settings, state_settings:
        with pytest.raises(ServiceUnavailableError) as exc:
            await post_workspace_installation_connect(
                workspace_id=workspace_id,
                current_user=_admin(workspace_id),
            )
    assert exc.value.error_code == "github_app_not_configured"


@pytest.mark.asyncio
async def test_connect_unavailable_when_secret_missing():
    workspace_id = uuid.uuid4()
    route_settings, state_settings = _settings(github_client_secret="")
    with route_settings, state_settings:
        with pytest.raises(ServiceUnavailableError) as exc:
            await post_workspace_installation_connect(
                workspace_id=workspace_id,
                current_user=_admin(workspace_id),
            )
    assert exc.value.error_code == "github_client_secret_missing"


def test_connect_plan_upgrade_required_on_free():
    workspace_id = uuid.uuid4()
    user = _admin(workspace_id)
    workspace = WorkspaceORM(
        slug="acme",
        name="Acme",
        status=WorkspaceStatus.active,
        plan=None,
    )
    workspace.id = workspace_id
    session = AsyncMock()
    session.get = AsyncMock(return_value=workspace)

    app = FastAPI()
    register_exception_handlers(app)
    app.include_router(router, prefix="/api/v1/workspaces")
    app.dependency_overrides[get_current_user] = lambda: user

    async def _db():
        yield session

    app.dependency_overrides[get_db] = _db
    client = TestClient(app)
    response = client.post(f"/api/v1/workspaces/{workspace_id}/installations/connect")
    assert response.status_code == 403
    assert response.json()["error"] == "plan_upgrade_required"


@pytest.mark.asyncio
async def test_verify_forbids_non_admin():
    workspace_id = uuid.uuid4()
    with pytest.raises(ForbiddenError) as exc:
        await post_workspace_installation_verify(
            workspace_id=workspace_id,
            installation_id=uuid.uuid4(),
            current_user=_viewer(workspace_id),
            session=AsyncMock(),
        )
    assert exc.value.error_code == "forbidden"


@pytest.mark.asyncio
async def test_verify_commits_after_live_list():
    from datetime import UTC, datetime

    from app.constants.enums import GitHubAccountType, GitHubInstallationStatus
    from app.models.github_installation import GitHubInstallationORM
    from app.schemas.github_installation import GitHubInstallationResponse

    workspace_id = uuid.uuid4()
    installation_id = uuid.uuid4()
    row = GitHubInstallationORM(
        workspace_id=workspace_id,
        github_installation_id=12345,
        account_login="acme",
        account_type=GitHubAccountType.organization,
        account_id=7,
        status=GitHubInstallationStatus.active,
    )
    row.id = installation_id
    row.created_at = datetime.now(UTC)
    row.updated_at = datetime.now(UTC)
    row.verified_at = datetime.now(UTC)
    session = AsyncMock()
    session.commit = AsyncMock()

    with (
        patch(
            "app.api.v1.workspaces.installations.get_github_installation",
            AsyncMock(return_value=row),
        ),
        patch(
            "app.api.v1.workspaces.installations.verify_granted_repositories",
            AsyncMock(return_value=row),
        ) as verify_mock,
        patch("app.api.v1.workspaces.installations.httpx.AsyncClient") as http_client_cls,
    ):
        http_client_cls.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
        http_client_cls.return_value.__aexit__ = AsyncMock(return_value=None)
        response = await post_workspace_installation_verify(
            workspace_id=workspace_id,
            installation_id=installation_id,
            current_user=_admin(workspace_id),
            session=session,
        )

    verify_mock.assert_awaited_once()
    session.commit.assert_awaited_once()
    assert isinstance(response.data, GitHubInstallationResponse)
    assert response.data.id == installation_id
