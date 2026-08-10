# backend/app/integrations/github_api.py
"""Minimal GitHub App API client — R1 repository list sync."""
from __future__ import annotations

import base64
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
import jwt

from app.core.config import settings
from app.core.exceptions import NotFoundError, RateLimitedError, ServiceUnavailableError
from app.core.logging import get_logger

GITHUB_API_BASE = "https://api.github.com"

REVIEW_THREADS_PAGE_SIZE = 100
REVIEW_THREAD_COMMENTS_PAGE_SIZE = 20
MAX_REVIEW_THREADS_PER_PUBLISH = 500

logger = get_logger(__name__)

_INDEXABLE_COMPARE_STATUSES = frozenset({"added", "modified", "copied", "renamed", "changed"})
_REMOVED_COMPARE_STATUSES = frozenset({"removed"})


def _graphql_errors_message(errors: list[Any]) -> str:
    parts: list[str] = []
    for err in errors:
        if isinstance(err, dict):
            parts.append(str(err.get("message") or err))
        else:
            parts.append(str(err))
    return "; ".join(parts)[:500]


def _is_graphql_client_error(errors: list[Any]) -> bool:
    for err in errors:
        if not isinstance(err, dict):
            continue
        message = (err.get("message") or "").lower()
        error_type = (err.get("type") or "").upper()
        if error_type in {"FORBIDDEN", "NOT_FOUND", "VALIDATION_FAILED"}:
            return True
        if "not accessible by integration" in message:
            return True
    return False


@dataclass(frozen=True)
class CompareFileChange:
    filename: str
    status: str
    patch: str | None
    previous_filename: str | None = None


@dataclass(frozen=True)
class CompareCommitsResult:
    files: tuple[CompareFileChange, ...]

    @property
    def paths_to_index(self) -> tuple[str, ...]:
        return tuple(
            f.filename
            for f in self.files
            if f.status in _INDEXABLE_COMPARE_STATUSES
        )

    @property
    def deleted_paths(self) -> tuple[str, ...]:
        return tuple(f.filename for f in self.files if f.status in _REMOVED_COMPARE_STATUSES)

    @property
    def renamed_from_paths(self) -> tuple[str, ...]:
        return tuple(
            f.previous_filename
            for f in self.files
            if f.status == "renamed" and f.previous_filename
        )

    @property
    def paths_to_remove(self) -> tuple[str, ...]:
        return self.deleted_paths + self.renamed_from_paths


def _compare_http_error(exc: httpx.HTTPStatusError) -> None:
    status_code = exc.response.status_code
    if status_code == 404:
        raise NotFoundError(
            message="GitHub compare not found",
            error_code="github_compare_not_found",
        ) from exc
    if status_code == 429:
        raise RateLimitedError(
            message="GitHub API rate limit exceeded",
            error_code="github_rate_limited",
        ) from exc
    raise exc


def _contents_http_error(exc: httpx.HTTPStatusError) -> None:
    status_code = exc.response.status_code
    if status_code == 404:
        raise NotFoundError(
            message="GitHub repository file not found",
            error_code="github_contents_not_found",
        ) from exc
    if status_code == 429:
        raise RateLimitedError(
            message="GitHub API rate limit exceeded",
            error_code="github_rate_limited",
        ) from exc
    raise exc


def _load_private_key() -> str:
    path = settings.github_app_private_key_path
    if not path:
        raise ServiceUnavailableError(
            message="GitHub App API is not configured",
            error_code="github_api_disabled",
        )
    return Path(path).read_text(encoding="utf-8")


def create_app_jwt() -> str:
    if not settings.github_api_enabled:
        raise ServiceUnavailableError(
            message="GitHub App API is not configured",
            error_code="github_api_disabled",
        )
    app_id = settings.github_app_id
    if not app_id:
        raise ServiceUnavailableError(
            message="GitHub App API is not configured",
            error_code="github_api_disabled",
        )
    now = int(time.time())
    # iat 60s in the past for clock drift; exp at most 600s after iat (GitHub max JWT lifetime).
    iat = now - 60
    payload = {"iat": iat, "exp": iat + 600, "iss": app_id}
    return jwt.encode(payload, _load_private_key(), algorithm="RS256")


async def _request(
    client: httpx.AsyncClient,
    method: str,
    url: str,
    *,
    headers: dict[str, str],
    params: dict[str, Any] | None = None,
) -> httpx.Response:
    response = await client.request(method, url, headers=headers, params=params)
    response.raise_for_status()
    return response


async def create_installation_access_token(
    client: httpx.AsyncClient,
    *,
    github_installation_id: int,
) -> str:
    app_jwt = create_app_jwt()
    response = await _request(
        client,
        "POST",
        f"{GITHUB_API_BASE}/app/installations/{github_installation_id}/access_tokens",
        headers={
            "Authorization": f"Bearer {app_jwt}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
    )
    data = response.json()
    token = data.get("token")
    if not isinstance(token, str):
        raise ServiceUnavailableError(
            message="GitHub installation token response invalid",
            error_code="github_api_error",
        )
    return token


async def list_installation_repositories(
    client: httpx.AsyncClient,
    *,
    github_installation_id: int,
) -> list[dict[str, Any]]:
    token = await create_installation_access_token(
        client,
        github_installation_id=github_installation_id,
    )
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    repos: list[dict[str, Any]] = []
    page = 1
    while True:
        response = await _request(
            client,
            "GET",
            f"{GITHUB_API_BASE}/installation/repositories",
            headers=headers,
            params={"per_page": 100, "page": page},
        )
        data = response.json()
        batch = data.get("repositories")
        if not isinstance(batch, list) or not batch:
            break
        for item in batch:
            if isinstance(item, dict):
                repos.append(item)
        if len(batch) < 100:
            break
        page += 1
    return repos


async def compare_commits(
    client: httpx.AsyncClient,
    *,
    github_installation_id: int,
    owner: str,
    repo: str,
    base_sha: str,
    head_sha: str,
    auth_headers: dict[str, str] | None = None,
) -> CompareCommitsResult:
    headers = await _resolve_auth_headers(
        client,
        github_installation_id=github_installation_id,
        auth_headers=auth_headers,
    )
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/compare/{base_sha}...{head_sha}"
    try:
        response = await client.get(url, headers=headers)
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        _compare_http_error(exc)
        raise  # pragma: no cover

    data = response.json()
    raw_files = data.get("files")
    if not isinstance(raw_files, list):
        return CompareCommitsResult(files=())

    if len(raw_files) >= 300:
        raise ServiceUnavailableError(
            message="GitHub compare returned too many changed files",
            error_code="github_compare_truncated",
        )

    files: list[CompareFileChange] = []
    for item in raw_files:
        if not isinstance(item, dict):
            continue
        filename = item.get("filename")
        status = item.get("status")
        if not isinstance(filename, str) or not isinstance(status, str):
            continue
        patch = item.get("patch")
        previous = item.get("previous_filename")
        files.append(
            CompareFileChange(
                filename=filename,
                status=status,
                patch=patch if isinstance(patch, str) else None,
                previous_filename=previous if isinstance(previous, str) else None,
            )
        )
    return CompareCommitsResult(files=tuple(files))


async def fetch_repository_file_at_sha(
    client: httpx.AsyncClient,
    *,
    github_installation_id: int,
    owner: str,
    repo: str,
    path: str,
    ref: str,
    auth_headers: dict[str, str] | None = None,
) -> str:
    """Fetch a single repository file at ref via GitHub Contents API."""
    headers = await _resolve_auth_headers(
        client,
        github_installation_id=github_installation_id,
        auth_headers=auth_headers,
    )
    encoded_path = quote(path, safe="/")
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/contents/{encoded_path}"
    try:
        response = await client.get(url, headers=headers, params={"ref": ref})
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        _contents_http_error(exc)
        raise  # pragma: no cover

    data = response.json()
    if not isinstance(data, dict):
        raise ServiceUnavailableError(
            message="GitHub contents response invalid",
            error_code="github_contents_invalid",
        )
    encoding = data.get("encoding")
    content = data.get("content")
    if encoding != "base64" or not isinstance(content, str):
        raise ServiceUnavailableError(
            message="GitHub contents response missing base64 body",
            error_code="github_contents_invalid",
        )
    return base64.b64decode(content).decode("utf-8")


async def get_pull_request(
    client: httpx.AsyncClient,
    *,
    github_installation_id: int,
    owner: str,
    repo: str,
    pull_number: int,
    auth_headers: dict[str, str] | None = None,
) -> dict[str, Any]:
    headers = await _resolve_auth_headers(
        client,
        github_installation_id=github_installation_id,
        auth_headers=auth_headers,
    )
    url = f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pull_number}"
    response = await client.get(url, headers=headers)
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise ServiceUnavailableError(
            message="GitHub pull request response invalid",
            error_code="github_pull_invalid",
        )
    return data


CHECK_RUN_NAME = "Revy"


def build_check_run_external_id(
    *,
    github_installation_id: int,
    github_pr_number: int,
    head_sha: str,
) -> str:
    return f"revy:{github_installation_id}:{github_pr_number}:{head_sha}"


async def _installation_headers(
    client: httpx.AsyncClient,
    *,
    github_installation_id: int,
) -> dict[str, str]:
    token = await create_installation_access_token(
        client,
        github_installation_id=github_installation_id,
    )
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


async def installation_auth_headers(
    client: httpx.AsyncClient,
    *,
    github_installation_id: int,
) -> dict[str, str]:
    return await _installation_headers(client, github_installation_id=github_installation_id)


async def _resolve_auth_headers(
    client: httpx.AsyncClient,
    *,
    github_installation_id: int,
    auth_headers: dict[str, str] | None,
) -> dict[str, str]:
    if auth_headers is not None:
        return auth_headers
    return await _installation_headers(client, github_installation_id=github_installation_id)


async def create_check_run(
    client: httpx.AsyncClient,
    *,
    github_installation_id: int,
    owner: str,
    repo: str,
    head_sha: str,
    external_id: str,
    status: str = "completed",
    conclusion: str | None = "neutral",
    summary: str = "",
    title: str = "Revy code review",
    auth_headers: dict[str, str] | None = None,
) -> int:
    headers = await _resolve_auth_headers(
        client,
        github_installation_id=github_installation_id,
        auth_headers=auth_headers,
    )
    payload: dict[str, Any] = {
        "name": CHECK_RUN_NAME,
        "head_sha": head_sha,
        "external_id": external_id,
        "status": status,
        "output": {"title": title, "summary": summary},
    }
    if status == "completed":
        payload["conclusion"] = conclusion or "neutral"
    response = await client.post(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/check-runs",
        headers=headers,
        json=payload,
    )
    response.raise_for_status()
    data = response.json()
    check_run_id = data.get("id")
    if not isinstance(check_run_id, int):
        raise ServiceUnavailableError(
            message="GitHub check run response invalid",
            error_code="github_api_error",
        )
    return check_run_id


async def update_check_run_in_progress(
    client: httpx.AsyncClient,
    *,
    github_installation_id: int,
    owner: str,
    repo: str,
    check_run_id: int,
    summary: str,
    title: str = "Revy code review",
    auth_headers: dict[str, str] | None = None,
) -> None:
    headers = await _resolve_auth_headers(
        client,
        github_installation_id=github_installation_id,
        auth_headers=auth_headers,
    )
    response = await client.patch(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/check-runs/{check_run_id}",
        headers=headers,
        json={
            "status": "in_progress",
            "output": {"title": title, "summary": summary},
        },
    )
    response.raise_for_status()


async def update_check_run(
    client: httpx.AsyncClient,
    *,
    github_installation_id: int,
    owner: str,
    repo: str,
    check_run_id: int,
    conclusion: str,
    summary: str,
    title: str = "Revy code review",
    auth_headers: dict[str, str] | None = None,
) -> None:
    headers = await _resolve_auth_headers(
        client,
        github_installation_id=github_installation_id,
        auth_headers=auth_headers,
    )
    response = await client.patch(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/check-runs/{check_run_id}",
        headers=headers,
        json={
            "status": "completed",
            "conclusion": conclusion,
            "output": {"title": title, "summary": summary},
        },
    )
    response.raise_for_status()


async def create_issue_comment(
    client: httpx.AsyncClient,
    *,
    github_installation_id: int,
    owner: str,
    repo: str,
    issue_number: int,
    body: str,
    auth_headers: dict[str, str] | None = None,
) -> int:
    headers = await _resolve_auth_headers(
        client,
        github_installation_id=github_installation_id,
        auth_headers=auth_headers,
    )
    response = await client.post(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/{issue_number}/comments",
        headers=headers,
        json={"body": body},
    )
    response.raise_for_status()
    data = response.json()
    comment_id = data.get("id")
    if not isinstance(comment_id, int):
        raise ServiceUnavailableError(
            message="GitHub issue comment response invalid",
            error_code="github_api_error",
        )
    return comment_id


async def update_issue_comment(
    client: httpx.AsyncClient,
    *,
    github_installation_id: int,
    owner: str,
    repo: str,
    comment_id: int,
    body: str,
    auth_headers: dict[str, str] | None = None,
) -> None:
    headers = await _resolve_auth_headers(
        client,
        github_installation_id=github_installation_id,
        auth_headers=auth_headers,
    )
    response = await client.patch(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/issues/comments/{comment_id}",
        headers=headers,
        json={"body": body},
    )
    response.raise_for_status()


async def create_pull_request_review_comment(
    client: httpx.AsyncClient,
    *,
    github_installation_id: int,
    owner: str,
    repo: str,
    pull_number: int,
    commit_id: str,
    path: str,
    line: int,
    body: str,
    auth_headers: dict[str, str] | None = None,
) -> int:
    headers = await _resolve_auth_headers(
        client,
        github_installation_id=github_installation_id,
        auth_headers=auth_headers,
    )
    response = await client.post(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/{pull_number}/comments",
        headers=headers,
        json={
            "body": body,
            "commit_id": commit_id,
            "path": path,
            "line": line,
            "side": "RIGHT",
        },
    )
    response.raise_for_status()
    data = response.json()
    comment_id = data.get("id")
    if not isinstance(comment_id, int) or comment_id <= 0:
        raise ServiceUnavailableError(
            message="GitHub pull request review comment response invalid",
            error_code="github_api_error",
        )
    return comment_id


async def delete_pull_request_review_comment(
    client: httpx.AsyncClient,
    *,
    github_installation_id: int,
    owner: str,
    repo: str,
    comment_id: int,
    auth_headers: dict[str, str] | None = None,
) -> None:
    headers = await _resolve_auth_headers(
        client,
        github_installation_id=github_installation_id,
        auth_headers=auth_headers,
    )
    response = await client.delete(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/pulls/comments/{comment_id}",
        headers=headers,
    )
    response.raise_for_status()


@dataclass(frozen=True)
class ReviewThreadNode:
    thread_id: str
    comment_database_ids: tuple[int, ...]
    is_outdated: bool = False
    is_resolved: bool = False


@dataclass(frozen=True)
class ReviewThreadIndex:
    """Maps REST review comment database id → GraphQL thread id plus collapse hints."""

    comment_to_thread_id: dict[int, str]
    outdated_comment_ids: frozenset[int]
    resolved_comment_ids: frozenset[int]


async def list_review_threads(
    client: httpx.AsyncClient,
    *,
    github_installation_id: int,
    owner: str,
    repo: str,
    pull_number: int,
    auth_headers: dict[str, str] | None = None,
) -> list[ReviewThreadNode]:
    """Paginated PR review threads with comment database ids."""
    headers = await _resolve_auth_headers(
        client,
        github_installation_id=github_installation_id,
        auth_headers=auth_headers,
    )
    threads: list[ReviewThreadNode] = []
    thread_cursor: str | None = None
    thread_query = f"""
    query($owner: String!, $repo: String!, $number: Int!, $threadCursor: String) {{
      repository(owner: $owner, name: $repo) {{
        pullRequest(number: $number) {{
          reviewThreads(first: {REVIEW_THREADS_PAGE_SIZE}, after: $threadCursor) {{
            pageInfo {{ hasNextPage endCursor }}
            nodes {{
              id
              isOutdated
              isResolved
              comments(first: {REVIEW_THREAD_COMMENTS_PAGE_SIZE}) {{
                pageInfo {{ hasNextPage endCursor }}
                nodes {{ databaseId }}
              }}
            }}
          }}
        }}
      }}
    }}
    """
    comment_page_query = f"""
    query($threadId: ID!, $commentCursor: String) {{
      node(id: $threadId) {{
        ... on PullRequestReviewThread {{
          comments(first: {REVIEW_THREAD_COMMENTS_PAGE_SIZE}, after: $commentCursor) {{
            pageInfo {{ hasNextPage endCursor }}
            nodes {{ databaseId }}
          }}
        }}
      }}
    }}
    """

    while True:
        if len(threads) >= MAX_REVIEW_THREADS_PER_PUBLISH:
            logger.warning(
                "github_list_review_threads_cap_hit",
                extra={"pull_number": pull_number, "thread_count": len(threads)},
            )
            break
        variables: dict[str, Any] = {
            "owner": owner,
            "repo": repo,
            "number": pull_number,
            "threadCursor": thread_cursor,
        }
        response = await client.post(
            f"{GITHUB_API_BASE}/graphql",
            headers=headers,
            json={"query": thread_query, "variables": variables},
        )
        response.raise_for_status()
        payload = response.json()
        if payload.get("errors"):
            logger.warning(
                "github_list_review_threads_graphql_error",
                extra={"pull_number": pull_number, "errors": payload.get("errors")},
            )
            break
        data = payload.get("data")
        if not isinstance(data, dict):
            break
        repository = data.get("repository")
        if not isinstance(repository, dict):
            break
        pull_request = repository.get("pullRequest")
        if not isinstance(pull_request, dict):
            break
        review_threads = pull_request.get("reviewThreads")
        if not isinstance(review_threads, dict):
            break
        nodes = review_threads.get("nodes", [])
        if not isinstance(nodes, list):
            break
        for thread in nodes:
            if len(threads) >= MAX_REVIEW_THREADS_PER_PUBLISH:
                logger.warning(
                    "github_list_review_threads_cap_hit",
                    extra={"pull_number": pull_number, "thread_count": len(threads)},
                )
                break
            if not isinstance(thread, dict):
                continue
            thread_id = thread.get("id")
            if not isinstance(thread_id, str) or not thread_id:
                continue
            is_outdated = thread.get("isOutdated") is True
            is_resolved = thread.get("isResolved") is True
            comment_ids: list[int] = []
            comments = thread.get("comments")
            if isinstance(comments, dict):
                comment_nodes = comments.get("nodes", [])
                if isinstance(comment_nodes, list):
                    for comment in comment_nodes:
                        if isinstance(comment, dict):
                            database_id = comment.get("databaseId")
                            if isinstance(database_id, int):
                                comment_ids.append(database_id)
                page_info = comments.get("pageInfo")
                if isinstance(page_info, dict) and page_info.get("hasNextPage"):
                    comment_cursor = page_info.get("endCursor")
                    while isinstance(comment_cursor, str):
                        comment_response = await client.post(
                            f"{GITHUB_API_BASE}/graphql",
                            headers=headers,
                            json={
                                "query": comment_page_query,
                                "variables": {
                                    "threadId": thread_id,
                                    "commentCursor": comment_cursor,
                                },
                            },
                        )
                        comment_response.raise_for_status()
                        comment_payload = comment_response.json()
                        if comment_payload.get("errors"):
                            logger.warning(
                                "github_list_review_threads_graphql_error",
                                extra={
                                    "pull_number": pull_number,
                                    "errors": comment_payload.get("errors"),
                                },
                            )
                            break
                        node = comment_payload.get("data", {}).get("node")
                        if not isinstance(node, dict):
                            break
                        more_comments = node.get("comments")
                        if not isinstance(more_comments, dict):
                            break
                        more_nodes = more_comments.get("nodes", [])
                        if isinstance(more_nodes, list):
                            for comment in more_nodes:
                                if isinstance(comment, dict):
                                    database_id = comment.get("databaseId")
                                    if isinstance(database_id, int):
                                        comment_ids.append(database_id)
                        more_page = more_comments.get("pageInfo")
                        if isinstance(more_page, dict) and more_page.get("hasNextPage"):
                            comment_cursor = more_page.get("endCursor")
                            if not isinstance(comment_cursor, str):
                                break
                        else:
                            break
            threads.append(
                ReviewThreadNode(
                    thread_id=thread_id,
                    comment_database_ids=tuple(comment_ids),
                    is_outdated=is_outdated,
                    is_resolved=is_resolved,
                )
            )
        page_info = review_threads.get("pageInfo")
        if not isinstance(page_info, dict) or not page_info.get("hasNextPage"):
            break
        thread_cursor = page_info.get("endCursor")
        if not isinstance(thread_cursor, str):
            break

    return threads


async def build_review_thread_index(
    client: httpx.AsyncClient,
    *,
    github_installation_id: int,
    owner: str,
    repo: str,
    pull_number: int,
    auth_headers: dict[str, str] | None = None,
) -> ReviewThreadIndex:
    """Map REST review comment database id → GraphQL thread id (PRRT_…)."""
    comment_to_thread_id: dict[int, str] = {}
    outdated_comment_ids: set[int] = set()
    resolved_comment_ids: set[int] = set()
    for thread in await list_review_threads(
        client,
        github_installation_id=github_installation_id,
        owner=owner,
        repo=repo,
        pull_number=pull_number,
        auth_headers=auth_headers,
    ):
        for comment_id in thread.comment_database_ids:
            comment_to_thread_id[comment_id] = thread.thread_id
            if thread.is_outdated:
                outdated_comment_ids.add(comment_id)
            if thread.is_resolved:
                resolved_comment_ids.add(comment_id)
    return ReviewThreadIndex(
        comment_to_thread_id=comment_to_thread_id,
        outdated_comment_ids=frozenset(outdated_comment_ids),
        resolved_comment_ids=frozenset(resolved_comment_ids),
    )


async def build_review_thread_comment_index(
    client: httpx.AsyncClient,
    *,
    github_installation_id: int,
    owner: str,
    repo: str,
    pull_number: int,
    auth_headers: dict[str, str] | None = None,
) -> dict[int, str]:
    """Map REST review comment database id → GraphQL thread id (PRRT_…)."""
    index = await build_review_thread_index(
        client,
        github_installation_id=github_installation_id,
        owner=owner,
        repo=repo,
        pull_number=pull_number,
        auth_headers=auth_headers,
    )
    return index.comment_to_thread_id


async def find_review_thread_id_for_comment(
    client: httpx.AsyncClient,
    *,
    github_installation_id: int,
    owner: str,
    repo: str,
    pull_number: int,
    comment_database_id: int,
    auth_headers: dict[str, str] | None = None,
    thread_index: dict[int, str] | None = None,
) -> str | None:
    """GraphQL lookup: REST comment id → review thread node id (PRRT_…)."""
    if thread_index is not None:
        cached = thread_index.get(comment_database_id)
        if cached is not None:
            return cached
    index = await build_review_thread_comment_index(
        client,
        github_installation_id=github_installation_id,
        owner=owner,
        repo=repo,
        pull_number=pull_number,
        auth_headers=auth_headers,
    )
    if thread_index is not None:
        index = {**thread_index, **index}
    return index.get(comment_database_id)


async def resolve_review_thread(
    client: httpx.AsyncClient,
    *,
    github_installation_id: int,
    thread_id: str,
    auth_headers: dict[str, str] | None = None,
) -> None:
    """Collapse a PR review thread on Files changed (GraphQL only)."""
    headers = await _resolve_auth_headers(
        client,
        github_installation_id=github_installation_id,
        auth_headers=auth_headers,
    )
    mutation = """
    mutation($threadId: ID!) {
      resolveReviewThread(input: {threadId: $threadId}) {
        thread { isResolved }
      }
    }
    """
    response = await client.post(
        f"{GITHUB_API_BASE}/graphql",
        headers=headers,
        json={"query": mutation, "variables": {"threadId": thread_id}},
    )
    response.raise_for_status()
    errors = response.json().get("errors")
    if errors:
        detail = _graphql_errors_message(errors)
        if _is_graphql_client_error(errors):
            request = httpx.Request("POST", f"{GITHUB_API_BASE}/graphql")
            response_payload = httpx.Response(
                403,
                request=request,
                json={"errors": errors},
            )
            raise httpx.HTTPStatusError(
                f"GitHub resolveReviewThread failed: {detail}",
                request=request,
                response=response_payload,
            )
        raise ServiceUnavailableError(
            message=f"GitHub resolveReviewThread failed: {detail}",
            error_code="github_api_error",
        )


def format_inline_comment_body(
    *,
    title: str,
    message: str,
    severity: str,
    suggestion: str | None = None,
) -> str:
    body = f"**[{severity.upper()}] {title}**\n\n{message}"
    if suggestion:
        body = f"{body}\n\n```suggestion\n{suggestion}\n```"
    return body

