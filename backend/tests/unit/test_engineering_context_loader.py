# backend/tests/unit/test_engineering_context_loader.py
"""RCX P1 — manifest loader at SHA."""
from unittest.mock import AsyncMock, patch

import pytest

from app.services.engineering_context.loader import load_review_context_manifest_at_sha


@pytest.mark.asyncio
async def test_load_review_context_manifest_at_sha():
    ssot = """
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
    client = AsyncMock()
    with patch(
        "app.services.engineering_context.loader.fetch_repository_file_at_sha",
        AsyncMock(return_value=ssot),
    ):
        manifest = await load_review_context_manifest_at_sha(
            client,
            github_installation_id=1,
            owner="org",
            repo="repo",
            head_sha="sha1",
        )
    assert manifest.active_program == "p"
