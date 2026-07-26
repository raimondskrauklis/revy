# backend/tests/unit/test_github_tasks.py
"""GitHub Celery tasks — R0 installation status sync."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.constants.enums import GitHubAccountType, GitHubInstallationStatus
from app.models.github_installation import GitHubInstallationORM
from app.models.github_webhook_delivery import GitHubWebhookDeliveryORM
from app.workers import github_tasks


@pytest.mark.asyncio
async def test_apply_installation_webhook_event_marks_removed():
    from app.services.github_installations import apply_installation_webhook_event

    installation = GitHubInstallationORM(
        workspace_id=uuid.uuid4(),
        github_installation_id=999,
        account_login="acme",
        account_type=GitHubAccountType.organization,
        account_id=1,
        status=GitHubInstallationStatus.active,
    )
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=installation)
    session.flush = AsyncMock()

    await apply_installation_webhook_event(
        session,
        github_installation_id=999,
        action="deleted",
    )

    assert installation.status == GitHubInstallationStatus.removed


def test_process_github_event_runs_installation_handler():
    delivery = GitHubWebhookDeliveryORM(
        delivery_id="d-1",
        event_type="installation",
        installation_id=12345,
        payload_json={
            "action": "suspend",
            "installation": {"id": 12345},
        },
    )
    session = AsyncMock()
    session.get = AsyncMock(return_value=delivery)

    db_context = MagicMock()
    db_context.__aenter__ = AsyncMock(return_value=session)
    db_context.__aexit__ = AsyncMock(return_value=None)

    with patch("app.workers.github_tasks.get_db_context", return_value=db_context):
        with patch(
            "app.workers.github_tasks.apply_installation_webhook_event",
            AsyncMock(),
        ) as apply_mock:
            github_tasks.process_github_event.run("d-1")

    apply_mock.assert_awaited_once()


def test_process_github_event_runs_installation_repositories_handler():
    delivery = GitHubWebhookDeliveryORM(
        delivery_id="d-2",
        event_type="installation_repositories",
        installation_id=12345,
        payload_json={
            "installation": {"id": 12345},
            "repositories_added": [],
        },
    )
    session = AsyncMock()
    session.get = AsyncMock(return_value=delivery)

    db_context = MagicMock()
    db_context.__aenter__ = AsyncMock(return_value=session)
    db_context.__aexit__ = AsyncMock(return_value=None)

    with patch("app.workers.github_tasks.get_db_context", return_value=db_context):
        with patch(
            "app.workers.github_tasks.apply_installation_repositories_webhook_event",
            AsyncMock(),
        ) as apply_mock:
            github_tasks.process_github_event.run("d-2")

    apply_mock.assert_awaited_once()


def test_process_github_event_runs_pull_request_handler():
    delivery = GitHubWebhookDeliveryORM(
        delivery_id="d-3",
        event_type="pull_request",
        installation_id=12345,
        payload_json={
            "action": "opened",
            "installation": {"id": 12345},
            "repository": {"id": 1},
            "pull_request": {"id": 2, "number": 1},
        },
    )
    session = AsyncMock()
    session.get = AsyncMock(return_value=delivery)

    db_context = MagicMock()
    db_context.__aenter__ = AsyncMock(return_value=session)
    db_context.__aexit__ = AsyncMock(return_value=None)

    with patch("app.workers.github_tasks.get_db_context", return_value=db_context):
        with patch(
            "app.workers.github_tasks.apply_pull_request_webhook_event",
            AsyncMock(),
        ) as apply_mock:
            github_tasks.process_github_event.run("d-3")

    apply_mock.assert_awaited_once()
