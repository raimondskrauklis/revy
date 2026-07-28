# backend/app/services/engineering_context/loader.py
"""Load SSOT manifest from GitHub at SHA (RCX P1)."""
from __future__ import annotations

import httpx

from app.integrations.github_api import fetch_repository_file_at_sha
from app.services.engineering_context.manifest import (
    SSOT_RELATIVE_PATH,
    parse_review_context_manifest_json,
)
from app.services.engineering_context.types import ReviewContextManifest


async def load_review_context_manifest_at_sha(
    client: httpx.AsyncClient,
    *,
    github_installation_id: int,
    owner: str,
    repo: str,
    head_sha: str,
) -> ReviewContextManifest:
    raw_text = await fetch_repository_file_at_sha(
        client,
        github_installation_id=github_installation_id,
        owner=owner,
        repo=repo,
        path=SSOT_RELATIVE_PATH,
        ref=head_sha,
    )
    return parse_review_context_manifest_json(raw_text)
