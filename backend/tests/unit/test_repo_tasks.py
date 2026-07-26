# backend/tests/unit/test_repo_tasks.py
"""Repository sync Celery tasks — R1."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.constants.enums import GitHubAccountType, GitHubInstallationStatus
from app.models.github_installation import GitHubInstallationORM
from app.workers import repo_tasks


def test_sync_installation_repositories_reconciles_repos():
    installation = GitHubInstallationORM(
        workspace_id=uuid.uuid4(),
        github_installation_id=55,
        account_login="acme",
        account_type=GitHubAccountType.organization,
        account_id=1,
        status=GitHubInstallationStatus.active,
    )
    installation.id = uuid.uuid4()

    session = AsyncMock()
    session.get = AsyncMock(return_value=installation)

    db_context = MagicMock()
    db_context.__aenter__ = AsyncMock(return_value=session)
    db_context.__aexit__ = AsyncMock(return_value=None)

    client = AsyncMock()
    client.__aenter__ = AsyncMock(return_value=client)
    client.__aexit__ = AsyncMock(return_value=None)

    with patch("app.workers.repo_tasks.get_db_context", return_value=db_context):
        with patch("app.workers.repo_tasks.httpx.AsyncClient", return_value=client):
            with patch(
                "app.workers.repo_tasks.list_installation_repositories",
                AsyncMock(return_value=[{"id": 1, "name": "a", "full_name": "acme/a"}]),
            ):
                with patch(
                    "app.workers.repo_tasks.reconcile_repositories_from_api",
                    AsyncMock(),
                ) as reconcile_mock:
                    repo_tasks.sync_installation_repositories.run(str(installation.id))

    reconcile_mock.assert_awaited_once()
