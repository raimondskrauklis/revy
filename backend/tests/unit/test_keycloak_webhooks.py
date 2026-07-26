# backend/tests/unit/test_keycloak_webhooks.py
"""Keycloak webhook dispatch — USER_PROVISIONING P1."""
from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import ServiceUnavailableError
from app.services.keycloak_webhooks import (
    apply_keycloak_webhook_event,
    delivery_id_from_payload,
    extract_email,
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


def test_extract_email_reads_updated_email():
    payload = {
        "type": "UPDATE_EMAIL",
        "userId": "kc-1",
        "details": {"updated_email": "new@example.com"},
    }
    assert extract_email(payload) == "new@example.com"


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
        await apply_keycloak_webhook_event(session, event_type="REGISTER", payload=payload)
    provision.assert_awaited_once()


@pytest.mark.asyncio
async def test_apply_update_email_uses_updated_email_field():
    session = AsyncMock()
    payload = {
        "type": "UPDATE_EMAIL",
        "userId": "kc-1",
        "details": {"updated_email": "new@example.com"},
    }
    with patch(
        "app.services.keycloak_webhooks.provision_user_from_keycloak",
        new_callable=AsyncMock,
    ) as provision:
        await apply_keycloak_webhook_event(session, event_type="UPDATE_EMAIL", payload=payload)
    provision.assert_awaited_once_with(
        session,
        sub="kc-1",
        email="new@example.com",
        email_verified=False,
        display_name=None,
    )


@pytest.mark.asyncio
async def test_apply_register_raises_when_user_id_missing():
    session = AsyncMock()
    with pytest.raises(ServiceUnavailableError) as exc_info:
        await apply_keycloak_webhook_event(
            session,
            event_type="REGISTER",
            payload={"type": "REGISTER"},
        )
    assert exc_info.value.error_code == "keycloak_webhook_missing_user_id"


@pytest.mark.asyncio
async def test_apply_delete_marks_user_deleted():
    session = AsyncMock()
    with patch(
        "app.services.keycloak_webhooks.apply_keycloak_user_deleted",
        new_callable=AsyncMock,
    ) as delete_user:
        await apply_keycloak_webhook_event(
            session,
            event_type="DELETE_ACCOUNT",
            payload={"userId": "kc-1"},
        )
    delete_user.assert_awaited_once_with(session, sub="kc-1")
