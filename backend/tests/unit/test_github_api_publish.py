# backend/tests/unit/test_github_api_publish.py
"""GitHub API publish client — R6."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.integrations import github_api


def test_build_check_run_external_id():
    external_id = github_api.build_check_run_external_id(
        github_installation_id=12345,
        github_pr_number=7,
        head_sha="abc123",
    )
    assert external_id == "revy:12345:7:abc123"


@pytest.mark.asyncio
async def test_create_check_run_returns_id():
    client = AsyncMock()
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {"id": 999}
    client.post = AsyncMock(return_value=response)

    with patch(
        "app.integrations.github_api._installation_headers",
        AsyncMock(return_value={"Authorization": "Bearer t"}),
    ):
        check_run_id = await github_api.create_check_run(
            client,
            github_installation_id=1,
            owner="acme",
            repo="demo",
            head_sha="sha",
            external_id="revy:1:2:sha",
            conclusion="success",
            summary="All good",
        )

    assert check_run_id == 999


@pytest.mark.asyncio
async def test_update_check_run_calls_patch():
    client = AsyncMock()
    response = MagicMock()
    response.raise_for_status = MagicMock()
    client.patch = AsyncMock(return_value=response)

    with patch(
        "app.integrations.github_api._installation_headers",
        AsyncMock(return_value={"Authorization": "Bearer t"}),
    ):
        await github_api.update_check_run(
            client,
            github_installation_id=1,
            owner="acme",
            repo="demo",
            check_run_id=999,
            conclusion="failure",
            summary="Issues found",
        )

    client.patch.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_issue_comment_returns_id():
    client = AsyncMock()
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {"id": 555}
    client.post = AsyncMock(return_value=response)

    with patch(
        "app.integrations.github_api._installation_headers",
        AsyncMock(return_value={"Authorization": "Bearer t"}),
    ):
        comment_id = await github_api.create_issue_comment(
            client,
            github_installation_id=1,
            owner="acme",
            repo="demo",
            issue_number=3,
            body="summary",
        )

    assert comment_id == 555


@pytest.mark.asyncio
async def test_create_pull_request_review_comment_posts():
    client = AsyncMock()
    response = MagicMock()
    response.raise_for_status = MagicMock()
    client.post = AsyncMock(return_value=response)

    with patch(
        "app.integrations.github_api._installation_headers",
        AsyncMock(return_value={"Authorization": "Bearer t"}),
    ):
        await github_api.create_pull_request_review_comment(
            client,
            github_installation_id=1,
            owner="acme",
            repo="demo",
            pull_number=3,
            commit_id="sha",
            path="app/main.py",
            line=10,
            body="issue",
        )

    client.post.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_check_run_reuses_provided_auth_headers():
    client = AsyncMock()
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {"id": 999}
    client.post = AsyncMock(return_value=response)
    headers_mock = AsyncMock()

    with patch("app.integrations.github_api._installation_headers", headers_mock):
        check_run_id = await github_api.create_check_run(
            client,
            github_installation_id=1,
            owner="acme",
            repo="demo",
            head_sha="sha",
            external_id="revy:1:2:sha",
            conclusion="success",
            summary="All good",
            auth_headers={"Authorization": "Bearer cached"},
        )

    assert check_run_id == 999
    headers_mock.assert_not_awaited()


def test_format_inline_comment_body():
    body = github_api.format_inline_comment_body(
        title="SQLi",
        message="Unsanitized",
        severity="error",
    )
    assert "SQLi" in body
    assert "ERROR" in body
