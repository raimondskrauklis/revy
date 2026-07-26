# backend/tests/unit/test_keycloak_webhooks.py
"""Keycloak webhook dispatch — USER_PROVISIONING P1."""
from unittest.mock import AsyncMock, patch

import pytest

from app.services.keycloak_webhooks import (
    apply_keycloak_webhook_event,
    delivery_id_from_payload,
    normalize_event_type,
    try_record_delivery,
)


@pytest.mark.asyncio
async def test_try_record_delivery_is_idempotent():
    session = AsyncMock()
    session.get = AsyncMock(return_value=None)
    session.add = lambda _row: None
    session.flush = AsyncMock()
    session.begin_nested = lambda: _Nested(session)

    first = await try_record_delivery(
        session,
        delivery_id="evt-1",
        event_type="REGISTER",
        payload={"userId": "kc-1"},
    )
    session.get = AsyncMock(return_value=object())
    second = await try_record_delivery(
        session,
        delivery_id="evt-1",
        event_type="REGISTER",
        payload={"userId": "kc-1"},
    )
    assert first is True
    assert second is False


class _Nested:
    def __init__(self, session: AsyncMock) -> None:
        self._session = session

    async def __aenter__(self) -> AsyncMock:
        return self._session

    async def __aexit__(self, *args: object) -> None:
        return None


def test_delivery_id_prefers_payload_id():
    payload = {"id": "evt-123", "userId": "kc-1", "time": 1}
    assert delivery_id_from_payload("REGISTER", payload) == "evt-123"


def test_delivery_id_hashes_when_no_id():
    payload = {"userId": "kc-1", "time": 99}
    first = delivery_id_from_payload("REGISTER", payload)
    second = delivery_id_from_payload("REGISTER", payload)
    assert first == second
    assert len(first) == 64


def test_normalize_event_type_from_payload():
    assert normalize_event_type({"type": "register"}, None) == "REGISTER"


@pytest.mark.asyncio
async def test_apply_register_provisions_user():
    session = AsyncMock()
    payload = {
        "type": "REGISTER",
        "userId": "kc-1",
        "details": {"email": "user@example.com", "email_verified": "true"},
    }
    with patch(
        "app.services.keycloak_webhooks.provision_user_from_keycloak",
        new_callable=AsyncMock,
    ) as provision:
        handled = await apply_keycloak_webhook_event(session, event_type="REGISTER", payload=payload)
    assert handled is True
    provision.assert_awaited_once()


@pytest.mark.asyncio
async def test_apply_delete_marks_user_deleted():
    session = AsyncMock()
    with patch(
        "app.services.keycloak_webhooks.apply_keycloak_user_deleted",
        new_callable=AsyncMock,
    ) as delete_user:
        handled = await apply_keycloak_webhook_event(
            session,
            event_type="DELETE_ACCOUNT",
            payload={"userId": "kc-1"},
        )
    assert handled is True
    delete_user.assert_awaited_once_with(session, sub="kc-1")
