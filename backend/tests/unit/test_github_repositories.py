# backend/tests/unit/test_github_repositories.py
"""GitHub repository service — R1 repository sync."""
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.constants.enums import GitHubAccountType, GitHubInstallationStatus, GitHubRepositoryStatus
from app.core.pagination import CursorParams
from app.models.github_installation import GitHubInstallationORM
from app.models.github_repository import GitHubRepositoryORM
from app.services.github_repositories import (
    apply_installation_repositories_webhook_event,
    list_github_repositories,
    reconcile_repositories_from_api,
    upsert_repository_from_github,
)


@pytest.mark.asyncio
async def test_upsert_repository_from_github_creates_row():
    installation = GitHubInstallationORM(
        workspace_id=uuid.uuid4(),
        github_installation_id=1,
        account_login="acme",
        account_type=GitHubAccountType.organization,
        account_id=2,
        status=GitHubInstallationStatus.active,
    )
    installation.id = uuid.uuid4()

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.flush = AsyncMock()

    row = await upsert_repository_from_github(
        session,
        installation=installation,
        repo={
            "id": 99,
            "name": "demo",
            "full_name": "acme/demo",
            "private": True,
            "default_branch": "main",
            "html_url": "https://github.com/acme/demo",
        },
    )

    session.add.assert_called_once()
    assert row is not None
    assert row.github_repository_id == 99
    assert row.status == GitHubRepositoryStatus.active


@pytest.mark.asyncio
async def test_apply_installation_repositories_webhook_event_adds_and_removes():
    workspace_id = uuid.uuid4()
    installation = GitHubInstallationORM(
        workspace_id=workspace_id,
        github_installation_id=42,
        account_login="acme",
        account_type=GitHubAccountType.organization,
        account_id=2,
        status=GitHubInstallationStatus.active,
    )
    installation.id = uuid.uuid4()

    existing = GitHubRepositoryORM(
        installation_id=installation.id,
        workspace_id=workspace_id,
        github_repository_id=100,
        name="old",
        full_name="acme/old",
        private=False,
        status=GitHubRepositoryStatus.active,
    )

    session = AsyncMock()

    async def scalar_side_effect(_stmt):
        return installation

    async def find_repo_side_effect(_session, *, installation_id, github_repository_id):
        if github_repository_id == 100:
            return existing
        return None

    session.scalar = AsyncMock(side_effect=scalar_side_effect)
    session.add = MagicMock()
    session.flush = AsyncMock()

    with patch(
        "app.services.github_repositories._find_repository",
        AsyncMock(side_effect=find_repo_side_effect),
    ):
        await apply_installation_repositories_webhook_event(
            session,
            {
                "installation": {"id": 42},
                "repositories_added": [
                    {"id": 200, "name": "new", "full_name": "acme/new", "private": False},
                ],
                "repositories_removed": [
                    {"id": 100, "name": "old", "full_name": "acme/old", "private": False},
                ],
            },
        )

    assert existing.status == GitHubRepositoryStatus.removed
    session.add.assert_called_once()


@pytest.mark.asyncio
async def test_reconcile_repositories_from_api_marks_missing_removed():
    workspace_id = uuid.uuid4()
    installation = GitHubInstallationORM(
        workspace_id=workspace_id,
        github_installation_id=7,
        account_login="acme",
        account_type=GitHubAccountType.organization,
        account_id=2,
        status=GitHubInstallationStatus.active,
    )
    installation.id = uuid.uuid4()

    stale = GitHubRepositoryORM(
        installation_id=installation.id,
        workspace_id=workspace_id,
        github_repository_id=1,
        name="stale",
        full_name="acme/stale",
        private=False,
        status=GitHubRepositoryStatus.active,
    )

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)
    session.scalars = AsyncMock(return_value=[stale])
    session.add = MagicMock()
    session.flush = AsyncMock()

    await reconcile_repositories_from_api(
        session,
        installation=installation,
        repos=[{"id": 2, "name": "fresh", "full_name": "acme/fresh", "private": False}],
    )

    assert stale.status == GitHubRepositoryStatus.removed


@pytest.mark.asyncio
async def test_list_github_repositories_returns_cursor_page():
    workspace_id = uuid.uuid4()
    installation_id = uuid.uuid4()
    installation = GitHubInstallationORM(
        workspace_id=workspace_id,
        github_installation_id=1,
        account_login="acme",
        account_type=GitHubAccountType.organization,
        account_id=2,
        status=GitHubInstallationStatus.active,
    )
    installation.id = installation_id

    row = GitHubRepositoryORM(
        installation_id=installation_id,
        workspace_id=workspace_id,
        github_repository_id=10,
        name="demo",
        full_name="acme/demo",
        private=False,
        status=GitHubRepositoryStatus.active,
    )
    row.id = uuid.uuid4()
    row.created_at = datetime.now(UTC)
    row.updated_at = datetime.now(UTC)

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=installation)
    session.scalars = AsyncMock(return_value=[row])

    page = await list_github_repositories(
        session,
        workspace_id=workspace_id,
        installation_id=installation_id,
        params=CursorParams(limit=50),
    )

    assert len(page.items) == 1
    assert page.items[0].full_name == "acme/demo"
