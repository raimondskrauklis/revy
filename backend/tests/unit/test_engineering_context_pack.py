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
async def test_build_engineering_context_pack_injects_when_changed_files_empty():
    """Compare-failure path: empty changed_files still loads locks (scope unknown)."""
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
                changed_files=[],
            )
    assert pack.active_program == "p"
    assert "RCX-D1" in pack.lock_ids
    assert "Locked decisions" in pack.inject_text


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


@pytest.mark.asyncio
async def test_build_engineering_context_pack_dedupes_full_md_in_diff():
    client = AsyncMock()
    ssot = """
    {
      "active_program": "p",
      "programs": [
        {
          "id": "p",
          "scope": ["backend/**"],
          "paths": [{"path": "backend/a.md", "description": "a"}]
        }
      ]
    }
    """
    manifest = parse_review_context_manifest_json(ssot)
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
                changed_files=["backend/a.md"],
                omitted_files=frozenset(),
                patches_by_file={"backend/a.md": "patch"},
            )
    assert pack.deduped_paths == ["backend/a.md"]
    assert "## Document:" not in pack.inject_text
    assert "Locked decisions" in pack.inject_text
