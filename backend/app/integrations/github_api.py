# backend/app/integrations/github_api.py
"""Minimal GitHub App API client — R1 repository list sync."""
from __future__ import annotations

import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import httpx
import jwt

from app.core.config import settings
from app.core.exceptions import NotFoundError, RateLimitedError, ServiceUnavailableError

GITHUB_API_BASE = "https://api.github.com"

_INDEXABLE_COMPARE_STATUSES = frozenset({"added", "modified", "copied", "renamed", "changed"})
_REMOVED_COMPARE_STATUSES = frozenset({"removed"})


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
    def paths_to_remove(self) -> tuple[str, ...]:
        removed: list[str] = []
        for f in self.files:
            if f.status in _REMOVED_COMPARE_STATUSES:
                removed.append(f.filename)
            elif f.status == "renamed" and f.previous_filename:
                removed.append(f.previous_filename)
        return tuple(removed)


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
    payload = {"iat": now - 60, "exp": now + 600, "iss": app_id}
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


CHECK_RUN_NAME = "revy/review"


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
    conclusion: str,
    summary: str,
    title: str = "Revy code review",
    auth_headers: dict[str, str] | None = None,
) -> int:
    headers = await _resolve_auth_headers(
        client,
        github_installation_id=github_installation_id,
        auth_headers=auth_headers,
    )
    response = await client.post(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/check-runs",
        headers=headers,
        json={
            "name": CHECK_RUN_NAME,
            "head_sha": head_sha,
            "external_id": external_id,
            "status": "completed",
            "conclusion": conclusion,
            "output": {"title": title, "summary": summary},
        },
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
) -> None:
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

