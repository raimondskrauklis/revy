# backend/tests/unit/test_stripe_webhook.py
"""Stripe webhook handler — signature verify, idempotency, dispatch."""
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from starlette.requests import Request

from app.api.v1.webhooks.stripe import post_stripe_webhook
from app.core.exceptions import ServiceUnavailableError, ValidationError


def _request_with_body(body: bytes) -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/webhooks/stripe",
        "headers": [],
    }

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    return Request(scope, receive)


@pytest.mark.asyncio
async def test_post_stripe_webhook_requires_signature():
    session = AsyncMock()
    request = _request_with_body(b"{}")

    with patch("app.api.v1.webhooks.stripe.settings") as mock_settings:
        mock_settings.stripe_enabled = True
        with pytest.raises(ValidationError):
            await post_stripe_webhook(
                request=request,
                session=session,
                stripe_signature=None,
            )


@pytest.mark.asyncio
async def test_post_stripe_webhook_disabled_raises():
    session = AsyncMock()
    request = _request_with_body(b"{}")

    with patch("app.api.v1.webhooks.stripe.settings") as mock_settings:
        mock_settings.stripe_enabled = False
        with pytest.raises(ServiceUnavailableError) as exc:
            await post_stripe_webhook(
                request=request,
                session=session,
                stripe_signature="sig",
            )

    assert exc.value.error_code == "billing_disabled"


@pytest.mark.asyncio
async def test_post_stripe_webhook_processes_new_event():
    session = AsyncMock()
    session.commit = AsyncMock()
    request = _request_with_body(b'{"id":"evt_1"}')
    event = {"id": "evt_1", "type": "checkout.session.completed", "data": {"object": {}}}
    stripe_client = MagicMock()
    stripe_client.construct_webhook_event.return_value = event

    with patch("app.api.v1.webhooks.stripe.settings") as mock_settings:
        mock_settings.stripe_enabled = True
        with patch(
            "app.api.v1.webhooks.stripe.get_stripe_client",
            return_value=stripe_client,
        ):
            with patch(
                "app.api.v1.webhooks.stripe.try_record_webhook_event",
                AsyncMock(return_value=True),
            ):
                with patch(
                    "app.api.v1.webhooks.stripe.apply_subscription_event",
                    AsyncMock(),
                ) as apply_mock:
                    response = await post_stripe_webhook(
                        request=request,
                        session=session,
                        stripe_signature="sig_test",
                    )

    assert response.status_code == 200
    apply_mock.assert_awaited_once()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_post_stripe_webhook_skips_duplicate_event():
    session = AsyncMock()
    session.commit = AsyncMock()
    request = _request_with_body(b'{"id":"evt_dup"}')
    event = {"id": "evt_dup", "type": "invoice.paid", "data": {"object": {}}}
    stripe_client = MagicMock()
    stripe_client.construct_webhook_event.return_value = event

    with patch("app.api.v1.webhooks.stripe.settings") as mock_settings:
        mock_settings.stripe_enabled = True
        with patch(
            "app.api.v1.webhooks.stripe.get_stripe_client",
            return_value=stripe_client,
        ):
            with patch(
                "app.api.v1.webhooks.stripe.try_record_webhook_event",
                AsyncMock(return_value=False),
            ):
                with patch(
                    "app.api.v1.webhooks.stripe.apply_subscription_event",
                    AsyncMock(),
                ) as apply_mock:
                    response = await post_stripe_webhook(
                        request=request,
                        session=session,
                        stripe_signature="sig_test",
                    )

    assert response.status_code == 200
    apply_mock.assert_not_awaited()
    session.commit.assert_awaited_once()
