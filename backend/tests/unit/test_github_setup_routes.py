# backend/tests/unit/test_github_setup_routes.py
"""Public GitHub Setup/Callback hops — github-onboarding P1."""
from unittest.mock import AsyncMock, MagicMock, patch
from urllib.parse import parse_qs, urlparse
from uuid import uuid4

from fastapi import FastAPI
from fastapi.testclient import TestClient

from app.api.v1.github_setup import router
from app.core.database import get_db
from app.core.exceptions import ForbiddenError
from app.services.github_install_state import SETUP_STASH_COOKIE, mint_install_state


def _settings(**overrides):
    values = {
        "github_client_secret": "github-client-secret",
        "github_client_id": "Iv1.client",
        "github_install_state_ttl_seconds": 1800,
        "github_callback_url": "http://localhost:8000/api/v1/github/callback",
        "github_setup_url": "http://localhost:8000/api/v1/github/setup",
        "app_public_url": "http://localhost:5173",
    }
    values.update(overrides)
    return patch(
        "app.api.v1.github_setup.settings",
        **values,
    )


def _state_settings():
    return patch(
        "app.services.github_install_state.settings",
        github_client_secret="github-client-secret",
        github_install_state_ttl_seconds=1800,
    )


def _client(*, session: AsyncMock | None = None) -> TestClient:
    app = FastAPI()
    app.include_router(router, prefix="/api/v1")
    if session is not None:

        async def _override_db():
            yield session

        app.dependency_overrides[get_db] = _override_db
    return TestClient(app, follow_redirects=False)


def test_get_setup_without_authorization_redirects_to_github():
    workspace_id = uuid4()
    user_id = uuid4()
    with _state_settings(), _settings():
        token = mint_install_state(workspace_id=workspace_id, user_id=user_id)
        client = _client()
        response = client.get(
            "/api/v1/github/setup",
            params={
                "state": token,
                "installation_id": "12345",
                "setup_action": "install",
            },
        )
    assert response.status_code == 302
    location = response.headers["location"]
    assert "https://github.com/login/oauth/authorize" in location
    assert "client_id=Iv1.client" in location
    assert SETUP_STASH_COOKIE in response.cookies


def test_get_callback_forged_installation_does_not_bind():
    workspace_id = uuid4()
    user_id = uuid4()
    session = AsyncMock()
    session.commit = AsyncMock()
    with _state_settings(), _settings():
        install_token = mint_install_state(workspace_id=workspace_id, user_id=user_id)
        client = _client(session=session)
        setup = client.get(
            "/api/v1/github/setup",
            params={"state": install_token, "installation_id": "999", "setup_action": "install"},
        )
        location = setup.headers["location"]
        oauth_state = parse_qs(urlparse(location).query)["state"][0]
        with (
            patch(
                "app.api.v1.github_setup.exchange_oauth_code",
                AsyncMock(return_value="ghu_test"),
            ),
            patch(
                "app.api.v1.github_setup.require_user_installation",
                AsyncMock(
                    side_effect=ForbiddenError(
                        message="mismatch",
                        error_code="github_installer_mismatch",
                    )
                ),
            ),
            patch("app.api.v1.github_setup.bind_github_installation") as bind_mock,
            patch("app.api.v1.github_setup.httpx.AsyncClient") as http_client_cls,
        ):
            http_client_cls.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
            http_client_cls.return_value.__aexit__ = AsyncMock(return_value=None)
            callback = client.get(
                "/api/v1/github/callback",
                params={"code": "abc", "state": oauth_state},
                cookies=setup.cookies,
            )
    assert callback.status_code == 302
    assert "setup_error=github_installer_mismatch" in callback.headers["location"]
    bind_mock.assert_not_called()
    session.commit.assert_not_called()


def test_get_callback_commits_then_enqueues():
    from app.constants.enums import GitHubAccountType
    from app.integrations.github_api import AppInstallationAccount

    workspace_id = uuid4()
    user_id = uuid4()
    bound_id = uuid4()
    session = AsyncMock()
    order: list[str] = []
    session.commit = AsyncMock(side_effect=lambda: order.append("commit"))
    bound = MagicMock()
    bound.id = bound_id
    with _state_settings(), _settings():
        install_token = mint_install_state(workspace_id=workspace_id, user_id=user_id)
        client = _client(session=session)
        setup = client.get(
            "/api/v1/github/setup",
            params={"state": install_token, "installation_id": "12345", "setup_action": "install"},
        )
        oauth_state = parse_qs(urlparse(setup.headers["location"]).query)["state"][0]
        with (
            patch(
                "app.api.v1.github_setup.exchange_oauth_code",
                AsyncMock(return_value="ghu_test"),
            ),
            patch(
                "app.api.v1.github_setup.require_user_installation",
                AsyncMock(),
            ),
            patch(
                "app.api.v1.github_setup.get_app_installation",
                AsyncMock(
                    return_value=AppInstallationAccount(
                        github_installation_id=12345,
                        account_login="acme",
                        account_type=GitHubAccountType.organization,
                        account_id=7,
                    )
                ),
            ),
            patch(
                "app.api.v1.github_setup.bind_github_installation",
                AsyncMock(return_value=bound),
            ) as bind_mock,
            patch(
                "app.api.v1.github_setup.enqueue_installation_repository_sync",
                side_effect=lambda *_args, **_kwargs: order.append("enqueue"),
            ),
            patch("app.api.v1.github_setup.httpx.AsyncClient") as http_client_cls,
        ):
            http_client_cls.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
            http_client_cls.return_value.__aexit__ = AsyncMock(return_value=None)
            callback = client.get(
                "/api/v1/github/callback",
                params={"code": "abc", "state": oauth_state},
                cookies=setup.cookies,
            )
    assert callback.status_code == 302
    assert "setup_error=" not in callback.headers["location"]
    bind_mock.assert_awaited_once()
    assert order == ["commit", "enqueue"]


def test_get_callback_github_http_error_redirects_to_spa():
    import httpx

    workspace_id = uuid4()
    user_id = uuid4()
    session = AsyncMock()
    session.commit = AsyncMock()
    with _state_settings(), _settings():
        install_token = mint_install_state(workspace_id=workspace_id, user_id=user_id)
        client = _client(session=session)
        setup = client.get(
            "/api/v1/github/setup",
            params={"state": install_token, "installation_id": "12345", "setup_action": "install"},
        )
        oauth_state = parse_qs(urlparse(setup.headers["location"]).query)["state"][0]
        with (
            patch(
                "app.api.v1.github_setup.exchange_oauth_code",
                AsyncMock(
                    side_effect=httpx.HTTPStatusError(
                        "upstream",
                        request=MagicMock(),
                        response=MagicMock(status_code=503),
                    )
                ),
            ),
            patch("app.api.v1.github_setup.bind_github_installation") as bind_mock,
            patch("app.api.v1.github_setup.httpx.AsyncClient") as http_client_cls,
        ):
            http_client_cls.return_value.__aenter__ = AsyncMock(return_value=MagicMock())
            http_client_cls.return_value.__aexit__ = AsyncMock(return_value=None)
            callback = client.get(
                "/api/v1/github/callback",
                params={"code": "abc", "state": oauth_state},
                cookies=setup.cookies,
            )
    assert callback.status_code == 302
    assert "setup_error=github_unavailable" in callback.headers["location"]
    bind_mock.assert_not_called()
    session.commit.assert_not_called()
