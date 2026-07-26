# backend/tests/unit/test_github_api.py
"""GitHub App API client — R1 repository list."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import ServiceUnavailableError
from app.integrations import github_api


def test_create_app_jwt_disabled_raises():
    with patch("app.integrations.github_api.settings") as mock_settings:
        mock_settings.github_api_enabled = False
        with pytest.raises(ServiceUnavailableError) as exc:
            github_api.create_app_jwt()
    assert exc.value.error_code == "github_api_disabled"


def test_create_app_jwt_returns_token():
    with patch("app.integrations.github_api.settings") as mock_settings:
        mock_settings.github_api_enabled = True
        mock_settings.github_app_id = "123"
        mock_settings.github_app_private_key_path = "/tmp/key.pem"
        with patch("app.integrations.github_api.Path.read_text", return_value="private-key"):
            with patch("app.integrations.github_api.jwt.encode", return_value="jwt-token") as encode:
                token = github_api.create_app_jwt()
    assert token == "jwt-token"
    encode.assert_called_once()
    payload = encode.call_args.args[0]
    assert payload["iss"] == "123"
    assert payload["exp"] - payload["iat"] == 660


@pytest.mark.asyncio
async def test_list_installation_repositories_paginates():
    client = AsyncMock()
    first = MagicMock()
    first.json.return_value = {
        "repositories": [{"id": 1, "name": "a", "full_name": "org/a"}],
    }
    first.raise_for_status = MagicMock()
    second = MagicMock()
    second.json.return_value = {"repositories": []}
    second.raise_for_status = MagicMock()

    client.request = AsyncMock(side_effect=[first, second])

    with patch(
        "app.integrations.github_api.create_installation_access_token",
        AsyncMock(return_value="install-token"),
    ):
        repos = await github_api.list_installation_repositories(
            client,
            github_installation_id=99,
        )

    assert len(repos) == 1
    assert repos[0]["full_name"] == "org/a"
