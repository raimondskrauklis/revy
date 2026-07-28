# backend/tests/unit/test_github_compare_patches.py
"""GitHub compare patches for judge — J-8."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.integrations.github_api import CompareCommitsResult, CompareFileChange
from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
from app.services.github_compare_patches import fetch_compare_patches_by_file


@pytest.mark.asyncio
async def test_fetch_compare_patches_by_file_returns_patches():
    pull_request = GitHubPullRequestORM(
        repository_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        installation_id=uuid.uuid4(),
        github_pull_request_id=1,
        number=42,
        title="PR",
        head_sha="head",
        head_ref="feature",
        base_ref="main",
    )
    pull_request.id = uuid.uuid4()
    revision = GitHubPullRequestRevisionORM(
        pull_request_id=pull_request.id,
        revision_number=1,
        head_sha="head",
        base_sha="base",
    )
    repository = MagicMock()
    repository.full_name = "acme/demo"
    installation = MagicMock()
    installation.github_installation_id = 99

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[repository, installation])

    compare = CompareCommitsResult(
        files=(
            CompareFileChange(
                filename="app/main.py",
                status="modified",
                patch="@@ -1 +1 @@\n+line\n",
            ),
        )
    )

    with patch(
        "app.services.github_compare_patches.compare_commits",
        AsyncMock(return_value=compare),
    ):
        patches = await fetch_compare_patches_by_file(
            session,
            pull_request=pull_request,
            revision=revision,
        )

    assert patches == {"app/main.py": "@@ -1 +1 @@\n+line\n"}


@pytest.mark.asyncio
async def test_fetch_compare_patches_by_file_missing_base_sha():
    pull_request = MagicMock()
    revision = MagicMock(base_sha=None, head_sha="head")
    session = AsyncMock()
    patches = await fetch_compare_patches_by_file(
        session,
        pull_request=pull_request,
        revision=revision,
    )
    assert patches == {}
