# backend/app/integrations/github_api.py
"""Minimal GitHub App API client — R1 repository list sync."""
from __future__ import annotations

import time
from pathlib import Path
from typing import Any

import httpx
import jwt

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError

GITHUB_API_BASE = "https://api.github.com"


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
