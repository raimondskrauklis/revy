# backend/tests/unit/test_engineering_context_pack.py
"""RCX P1 — engineering context pack orchestration."""
import binascii
from unittest.mock import AsyncMock, patch

import pytest

from app.services.engineering_context.manifest import parse_review_context_manifest_json
from app.services.engineering_context.pack import build_engineering_context_pack

_SSOT = """
{
  "active_program": "p",
  "programs": [
    {
      "id": "p",
      "scope": ["backend/**"],
      "paths": [{"path": "docs/a.md", "description": "a"}]
    }
  ]
}
"""


@pytest.mark.asyncio
async def test_build_engineering_context_pack_scope_mismatch_returns_empty():
    client = AsyncMock()
    manifest = parse_review_context_manifest_json(_SSOT)
    with patch(
        "app.services.engineering_context.pack.load_review_context_manifest_at_sha",
        AsyncMock(return_value=manifest),
    ):
        pack = await build_engineering_context_pack(
            client,
            github_installation_id=1,
            owner="org",
            repo="repo",
            head_sha="sha1",
            changed_files=["frontend/foo.tsx"],
        )
    assert pack.extracted_text == ""
    assert pack.active_program is None


@pytest.mark.asyncio
async def test_build_engineering_context_pack_extracts_locks():
    client = AsyncMock()
    manifest = parse_review_context_manifest_json(_SSOT)
    md = "## Locked decisions\n\n| **RCX-D1** | lock |\n"
    with patch(
        "app.services.engineering_context.pack.load_review_context_manifest_at_sha",
        AsyncMock(return_value=manifest),
    ):
        with patch(
            "app.services.engineering_context.pack.fetch_repository_file_at_sha",
            AsyncMock(return_value=md),
        ):
            pack = await build_engineering_context_pack(
                client,
                github_installation_id=1,
                owner="org",
                repo="repo",
                head_sha="sha1",
                changed_files=["backend/main.py"],
            )
    assert pack.active_program == "p"
    assert "RCX-D1" in pack.lock_ids
    assert "Locked decisions" in pack.extracted_text


@pytest.mark.asyncio
async def test_build_engineering_context_pack_catches_malformed_base64():
    client = AsyncMock()
    manifest = parse_review_context_manifest_json(_SSOT)
    with patch(
        "app.services.engineering_context.pack.load_review_context_manifest_at_sha",
        AsyncMock(return_value=manifest),
    ):
        with patch(
            "app.services.engineering_context.pack.fetch_repository_file_at_sha",
            AsyncMock(side_effect=binascii.Error("invalid base64")),
        ):
            pack = await build_engineering_context_pack(
                client,
                github_installation_id=1,
                owner="org",
                repo="repo",
                head_sha="sha1",
                changed_files=["backend/main.py"],
            )
    assert pack.extracted_text == ""
    assert any("fetch_failed" in err for err in pack.errors)
