# backend/tests/unit/test_github_api.py
"""GitHub App API client — R1 repository list."""
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core.exceptions import NotFoundError, RateLimitedError, ServiceUnavailableError
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


@pytest.mark.asyncio
async def test_list_installation_repositories_raises_on_http_error():
    client = AsyncMock()
    error_response = MagicMock()
    error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "error",
        request=MagicMock(),
        response=MagicMock(status_code=503),
    )
    client.request = AsyncMock(return_value=error_response)

    with patch(
        "app.integrations.github_api.create_installation_access_token",
        AsyncMock(return_value="install-token"),
    ):
        with pytest.raises(httpx.HTTPStatusError):
            await github_api.list_installation_repositories(
                client,
                github_installation_id=99,
            )


@pytest.mark.asyncio
async def test_compare_commits_returns_changed_paths():
    client = AsyncMock()
    response = MagicMock()
    response.json.return_value = {
        "files": [
            {"filename": "a.py", "status": "modified", "patch": "@@"},
            {"filename": "b.py", "status": "removed"},
            {
                "filename": "c.py",
                "status": "renamed",
                "previous_filename": "old_c.py",
            },
        ],
    }
    response.raise_for_status = MagicMock()
    client.get = AsyncMock(return_value=response)

    with patch(
        "app.integrations.github_api._installation_headers",
        AsyncMock(return_value={"Authorization": "Bearer t"}),
    ):
        result = await github_api.compare_commits(
            client,
            github_installation_id=1,
            owner="acme",
            repo="demo",
            base_sha="base",
            head_sha="head",
        )

    assert result.paths_to_index == ("a.py", "c.py")
    assert result.deleted_paths == ("b.py",)
    assert result.renamed_from_paths == ("old_c.py",)
    assert result.paths_to_remove == ("b.py", "old_c.py")


@pytest.mark.asyncio
async def test_compare_commits_404_raises_not_found():
    client = AsyncMock()
    error_response = MagicMock(status_code=404)
    client.get = AsyncMock(
        side_effect=httpx.HTTPStatusError(
            "missing",
            request=MagicMock(),
            response=error_response,
        ),
    )

    with patch(
        "app.integrations.github_api._installation_headers",
        AsyncMock(return_value={"Authorization": "Bearer t"}),
    ):
        with pytest.raises(NotFoundError) as exc:
            await github_api.compare_commits(
                client,
                github_installation_id=1,
                owner="acme",
                repo="demo",
                base_sha="base",
                head_sha="head",
            )
    assert exc.value.error_code == "github_compare_not_found"


@pytest.mark.asyncio
async def test_compare_commits_429_raises_rate_limited():
    client = AsyncMock()
    error_response = MagicMock(status_code=429)
    client.get = AsyncMock(
        side_effect=httpx.HTTPStatusError(
            "rate",
            request=MagicMock(),
            response=error_response,
        ),
    )

    with patch(
        "app.integrations.github_api._installation_headers",
        AsyncMock(return_value={"Authorization": "Bearer t"}),
    ):
        with pytest.raises(RateLimitedError) as exc:
            await github_api.compare_commits(
                client,
                github_installation_id=1,
                owner="acme",
                repo="demo",
                base_sha="base",
                head_sha="head",
            )
    assert exc.value.error_code == "github_rate_limited"


@pytest.mark.asyncio
async def test_get_pull_request_returns_payload():
    client = AsyncMock()
    response = MagicMock()
    response.json.return_value = {"number": 42, "body": "Fixes #1"}
    response.raise_for_status = MagicMock()
    client.get = AsyncMock(return_value=response)

    with patch(
        "app.integrations.github_api._installation_headers",
        AsyncMock(return_value={"Authorization": "Bearer t"}),
    ):
        data = await github_api.get_pull_request(
            client,
            github_installation_id=1,
            owner="acme",
            repo="demo",
            pull_number=42,
        )

    assert data["body"] == "Fixes #1"


@pytest.mark.asyncio
async def test_list_installation_repositories_raises_on_mid_pagination_error():
    client = AsyncMock()
    first = MagicMock()
    first.json.return_value = {
        "repositories": [{"id": i, "name": f"r{i}", "full_name": f"org/r{i}"} for i in range(100)],
    }
    first.raise_for_status = MagicMock()
    error_response = MagicMock()
    error_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "error",
        request=MagicMock(),
        response=MagicMock(status_code=503),
    )
    client.request = AsyncMock(side_effect=[first, error_response])

    with patch(
        "app.integrations.github_api.create_installation_access_token",
        AsyncMock(return_value="install-token"),
    ):
        with pytest.raises(httpx.HTTPStatusError):
            await github_api.list_installation_repositories(
                client,
                github_installation_id=99,
            )


@pytest.mark.asyncio
async def test_fetch_repository_file_at_sha_decodes_base64():
    client = AsyncMock()
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {
        "encoding": "base64",
        "content": "aGVsbG8=",
    }
    client.get = AsyncMock(return_value=response)

    with patch(
        "app.integrations.github_api._resolve_auth_headers",
        AsyncMock(return_value={"Authorization": "token"}),
    ):
        text = await github_api.fetch_repository_file_at_sha(
            client,
            github_installation_id=1,
            owner="org",
            repo="repo",
            path=".revy/review-context.json",
            ref="abc123",
        )

    assert text == "hello"


@pytest.mark.asyncio
async def test_fetch_repository_file_at_sha_url_encodes_path():
    client = AsyncMock()
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {
        "encoding": "base64",
        "content": "aGVsbG8=",
    }
    client.get = AsyncMock(return_value=response)

    with patch(
        "app.integrations.github_api._resolve_auth_headers",
        AsyncMock(return_value={"Authorization": "token"}),
    ):
        await github_api.fetch_repository_file_at_sha(
            client,
            github_installation_id=1,
            owner="org",
            repo="repo",
            path="docs/foo bar.md",
            ref="abc123",
        )

    called_url = client.get.await_args.args[0]
    assert "foo%20bar.md" in called_url


@pytest.mark.asyncio
async def test_fetch_repository_file_at_sha_404_raises_not_found():
    client = AsyncMock()
    client.get = AsyncMock(
        side_effect=httpx.HTTPStatusError(
            "missing",
            request=MagicMock(),
            response=MagicMock(status_code=404),
        )
    )

    with patch(
        "app.integrations.github_api._resolve_auth_headers",
        AsyncMock(return_value={"Authorization": "token"}),
    ):
        with pytest.raises(NotFoundError) as exc:
            await github_api.fetch_repository_file_at_sha(
                client,
                github_installation_id=1,
                owner="org",
                repo="repo",
                path="missing.md",
                ref="abc123",
            )
    assert exc.value.error_code == "github_contents_not_found"
