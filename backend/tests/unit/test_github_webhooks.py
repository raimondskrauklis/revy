# backend/tests/unit/test_github_webhooks.py
"""GitHub webhook service — delivery dedupe and dispatch ordering."""
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError

from app.services.github_webhooks import (
    SUPPORTED_EVENTS,
    accept_github_webhook,
    enqueue_github_event,
    try_record_delivery,
)


class _UniqueViolation(Exception):
    pgcode = "23505"


def _session_with_nested() -> AsyncMock:
    session = AsyncMock()
    session.get = AsyncMock(return_value=None)
    session.add = MagicMock()
    session.flush = AsyncMock()

    @asynccontextmanager
    async def _begin_nested():
        yield

    session.begin_nested = MagicMock(side_effect=_begin_nested)
    return session


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
    session = _session_with_nested()

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
    session.begin_nested.assert_called_once()


@pytest.mark.asyncio
async def test_try_record_delivery_treats_unique_violation_as_duplicate():
    session = _session_with_nested()
    session.flush = AsyncMock(
        side_effect=IntegrityError("insert", {}, _UniqueViolation("unique")),
    )

    is_new = await try_record_delivery(
        session,
        delivery_id="delivery-1",
        event_type="installation",
        installation_id=1,
        payload={"installation": {"id": 1}},
    )

    assert is_new is False
    session.rollback.assert_not_called()


@pytest.mark.asyncio
async def test_try_record_delivery_reraises_non_unique_integrity_error():
    session = _session_with_nested()
    session.flush = AsyncMock(
        side_effect=IntegrityError("insert", {}, Exception("not_null")),
    )

    with pytest.raises(IntegrityError):
        await try_record_delivery(
            session,
            delivery_id="delivery-1",
            event_type="installation",
            installation_id=1,
            payload={"installation": {"id": 1}},
        )


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
    # enqueue_github_event imports process_github_event at call time.
    with patch("app.workers.github_tasks.process_github_event") as task_mock:
        enqueue_github_event("delivery-1")

    task_mock.delay.assert_called_once_with("delivery-1")


def test_supported_events_includes_issue_comment():
    assert "issue_comment" in SUPPORTED_EVENTS
