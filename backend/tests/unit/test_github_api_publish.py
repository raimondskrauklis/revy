# backend/tests/unit/test_github_api_publish.py
"""GitHub API publish client — R6."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import ServiceUnavailableError
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
    response.json.return_value = {"id": 999}
    client.post = AsyncMock(return_value=response)

    with patch(
        "app.integrations.github_api._resolve_auth_headers",
        AsyncMock(return_value={"Authorization": "Bearer t"}),
    ):
        comment_id = await github_api.create_pull_request_review_comment(
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

    assert comment_id == 999
    client.post.assert_awaited_once()


@pytest.mark.asyncio
async def test_create_pull_request_review_comment_rejects_zero_id():
    client = AsyncMock()
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {"id": 0}
    client.post = AsyncMock(return_value=response)

    with patch(
        "app.integrations.github_api._resolve_auth_headers",
        AsyncMock(return_value={"Authorization": "Bearer t"}),
    ):
        with pytest.raises(ServiceUnavailableError):
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


@pytest.mark.asyncio
async def test_find_review_thread_id_for_comment_skips_null_comment_nodes():
    client = AsyncMock()
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {
        "data": {
            "repository": {
                "pullRequest": {
                    "reviewThreads": {
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                        "nodes": [
                            {
                                "id": "PRRT_1",
                                "comments": {
                                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                                    "nodes": [None, {"databaseId": 42}],
                                },
                            }
                        ],
                    }
                }
            }
        }
    }
    client.post = AsyncMock(return_value=response)

    with patch(
        "app.integrations.github_api._resolve_auth_headers",
        AsyncMock(return_value={"Authorization": "Bearer t"}),
    ):
        thread_id = await github_api.find_review_thread_id_for_comment(
            client,
            github_installation_id=1,
            owner="acme",
            repo="demo",
            pull_number=3,
            comment_database_id=42,
        )

    assert thread_id == "PRRT_1"


@pytest.mark.asyncio
async def test_find_review_thread_id_for_comment_falls_back_on_cache_miss():
    client = AsyncMock()
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {
        "data": {
            "repository": {
                "pullRequest": {
                    "reviewThreads": {
                        "pageInfo": {"hasNextPage": False, "endCursor": None},
                        "nodes": [
                            {
                                "id": "PRRT_miss",
                                "comments": {
                                    "pageInfo": {"hasNextPage": False, "endCursor": None},
                                    "nodes": [{"databaseId": 77}],
                                },
                            }
                        ],
                    }
                }
            }
        }
    }
    client.post = AsyncMock(return_value=response)

    with patch(
        "app.integrations.github_api._resolve_auth_headers",
        AsyncMock(return_value={"Authorization": "Bearer t"}),
    ):
        thread_id = await github_api.find_review_thread_id_for_comment(
            client,
            github_installation_id=1,
            owner="acme",
            repo="demo",
            pull_number=3,
            comment_database_id=77,
            thread_index={99: "PRRT_other"},
        )

    assert thread_id == "PRRT_miss"


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


def test_format_inline_comment_body_with_suggestion():
    body = github_api.format_inline_comment_body(
        title="SQLi",
        message="Unsanitized",
        severity="error",
        suggestion="safe_query()",
    )
    assert "```suggestion" in body
    assert "safe_query()" in body


@pytest.mark.asyncio
async def test_find_review_thread_id_for_comment_returns_none_on_null_graphql_data():
    client = AsyncMock()
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {"data": None}
    client.post = AsyncMock(return_value=response)

    with patch(
        "app.integrations.github_api._resolve_auth_headers",
        AsyncMock(return_value={"Authorization": "Bearer t"}),
    ):
        thread_id = await github_api.find_review_thread_id_for_comment(
            client,
            github_installation_id=1,
            owner="acme",
            repo="demo",
            pull_number=3,
            comment_database_id=42,
        )

    assert thread_id is None


def _thread_page(nodes: list, *, has_next: bool = False, end_cursor: str | None = None) -> dict:
    return {
        "pageInfo": {"hasNextPage": has_next, "endCursor": end_cursor},
        "nodes": nodes,
    }


def _thread_node(thread_id: str, comment_ids: list[int], *, comments_has_next: bool = False) -> dict:
    return {
        "id": thread_id,
        "comments": {
            "pageInfo": {"hasNextPage": comments_has_next, "endCursor": "cmt-cursor" if comments_has_next else None},
            "nodes": [{"databaseId": cid} for cid in comment_ids],
        },
    }


@pytest.mark.asyncio
async def test_list_review_threads_pagination():
    client = AsyncMock()
    page_one = MagicMock()
    page_one.raise_for_status = MagicMock()
    page_one.json.return_value = {
        "data": {
            "repository": {
                "pullRequest": {
                    "reviewThreads": _thread_page(
                        [_thread_node("PRRT_1", [41])],
                        has_next=True,
                        end_cursor="thread-cursor-1",
                    )
                }
            }
        }
    }
    page_two = MagicMock()
    page_two.raise_for_status = MagicMock()
    page_two.json.return_value = {
        "data": {
            "repository": {
                "pullRequest": {
                    "reviewThreads": _thread_page(
                        [_thread_node("PRRT_2", [42])],
                    )
                }
            }
        }
    }
    client.post = AsyncMock(side_effect=[page_one, page_two])

    with patch(
        "app.integrations.github_api._resolve_auth_headers",
        AsyncMock(return_value={"Authorization": "Bearer t"}),
    ):
        threads = await github_api.list_review_threads(
            client,
            github_installation_id=1,
            owner="acme",
            repo="demo",
            pull_number=3,
        )

    assert len(threads) == 2
    assert threads[0].thread_id == "PRRT_1"
    assert threads[1].comment_database_ids == (42,)
    assert client.post.await_count == 2


@pytest.mark.asyncio
async def test_list_review_threads_cap_hit(caplog):
    client = AsyncMock()
    response = MagicMock()
    response.raise_for_status = MagicMock()
    nodes = [_thread_node(f"PRRT_{i}", [i]) for i in range(github_api.MAX_REVIEW_THREADS_PER_PUBLISH)]
    response.json.return_value = {
        "data": {
            "repository": {
                "pullRequest": {
                    "reviewThreads": _thread_page(nodes, has_next=True, end_cursor="more"),
                }
            }
        }
    }
    client.post = AsyncMock(return_value=response)

    with patch(
        "app.integrations.github_api._resolve_auth_headers",
        AsyncMock(return_value={"Authorization": "Bearer t"}),
    ):
        with caplog.at_level("WARNING"):
            threads = await github_api.list_review_threads(
                client,
                github_installation_id=1,
                owner="acme",
                repo="demo",
                pull_number=3,
            )

    assert len(threads) == github_api.MAX_REVIEW_THREADS_PER_PUBLISH
    assert "github_list_review_threads_cap_hit" in caplog.text


@pytest.mark.asyncio
async def test_build_review_thread_comment_index_maps_ids():
    with patch(
        "app.integrations.github_api.list_review_threads",
        AsyncMock(
            return_value=[
                github_api.ReviewThreadNode(thread_id="PRRT_a", comment_database_ids=(10, 11)),
                github_api.ReviewThreadNode(thread_id="PRRT_b", comment_database_ids=(20,)),
            ]
        ),
    ):
        index = await github_api.build_review_thread_comment_index(
            AsyncMock(),
            github_installation_id=1,
            owner="acme",
            repo="demo",
            pull_number=3,
        )

    assert index == {10: "PRRT_a", 11: "PRRT_a", 20: "PRRT_b"}


@pytest.mark.asyncio
async def test_list_review_threads_logs_graphql_errors(caplog):
    client = AsyncMock()
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {
        "errors": [{"message": "rate limit"}],
        "data": None,
    }
    client.post = AsyncMock(return_value=response)

    with patch(
        "app.integrations.github_api._resolve_auth_headers",
        AsyncMock(return_value={"Authorization": "Bearer t"}),
    ):
        with caplog.at_level("WARNING"):
            threads = await github_api.list_review_threads(
                client,
                github_installation_id=1,
                owner="acme",
                repo="demo",
                pull_number=3,
            )

    assert threads == []
    assert "github_list_review_threads_graphql_error" in caplog.text
