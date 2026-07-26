# backend/tests/unit/test_github_webhooks.py
"""GitHub webhook service — delivery dedupe and dispatch ordering."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from app.services.github_webhooks import (
    accept_github_webhook,
    enqueue_github_event,
    try_record_delivery,
)


@pytest.mark.asyncio
async def test_try_record_delivery_returns_false_for_existing():
    session = AsyncMock()
    session.get = AsyncMock(return_value=MagicMock())

    is_new = await try_record_delivery(
        session,
        delivery_id="delivery-1",
        event_type="installation",
        installation_id=1,
        payload={"installation": {"id": 1}},
    )

    assert is_new is False
    session.add.assert_not_called()


@pytest.mark.asyncio
async def test_try_record_delivery_persists_new_delivery():
    session = AsyncMock()
    session.get = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.flush = AsyncMock()

    is_new = await try_record_delivery(
        session,
        delivery_id="delivery-1",
        event_type="installation",
        installation_id=1,
        payload={"installation": {"id": 1}},
    )

    assert is_new is True
    session.add.assert_called_once()
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_try_record_delivery_treats_integrity_error_as_duplicate():
    session = AsyncMock()
    session.get = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.flush = AsyncMock(side_effect=IntegrityError("insert", {}, Exception("unique")))
    session.rollback = AsyncMock()

    is_new = await try_record_delivery(
        session,
        delivery_id="delivery-1",
        event_type="installation",
        installation_id=1,
        payload={"installation": {"id": 1}},
    )

    assert is_new is False
    session.rollback.assert_awaited_once()


@pytest.mark.asyncio
async def test_accept_github_webhook_does_not_enqueue():
    session = AsyncMock()
    payload = {"installation": {"id": 1}}

    with patch(
        "app.services.github_webhooks.try_record_delivery",
        AsyncMock(return_value=True),
    ):
        with patch("app.services.github_webhooks.enqueue_github_event") as enqueue_mock:
            accepted = await accept_github_webhook(
                session,
                delivery_id="delivery-1",
                event_type="installation",
                payload=payload,
            )

    assert accepted is True
    enqueue_mock.assert_not_called()


@pytest.mark.asyncio
async def test_accept_github_webhook_ignores_unsupported_events():
    session = AsyncMock()

    with patch("app.services.github_webhooks.enqueue_github_event") as enqueue_mock:
        accepted = await accept_github_webhook(
            session,
            delivery_id="delivery-1",
            event_type="ping",
            payload={},
        )

    assert accepted is False
    enqueue_mock.assert_not_called()


def test_enqueue_github_event_dispatches_celery_task():
    with patch("app.workers.github_tasks.process_github_event") as task_mock:
        enqueue_github_event("delivery-1")

    task_mock.delay.assert_called_once_with("delivery-1")
