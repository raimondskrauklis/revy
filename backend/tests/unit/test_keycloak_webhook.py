# backend/tests/unit/test_keycloak_webhook.py
"""Keycloak webhook handler — USER_PROVISIONING P1."""
import json
from unittest.mock import AsyncMock, patch

import pytest
from starlette.requests import Request

from app.api.v1.webhooks.keycloak import post_keycloak_webhook
from app.core.exceptions import ServiceUnavailableError, UnauthorizedError, ValidationError


def _request_with_body(body: bytes) -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/webhooks/keycloak",
        "headers": [],
    }

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    return Request(scope, receive)


@pytest.mark.asyncio
async def test_post_keycloak_webhook_disabled_raises():
    session = AsyncMock()
    request = _request_with_body(b"{}")

    with patch("app.api.v1.webhooks.keycloak.settings") as mock_settings:
        mock_settings.keycloak_webhooks_enabled = False
        with pytest.raises(ServiceUnavailableError) as exc:
            await post_keycloak_webhook(
                request=request,
                session=session,
                webhook_secret="secret",
            )

    assert exc.value.error_code == "keycloak_webhooks_disabled"


@pytest.mark.asyncio
async def test_post_keycloak_webhook_requires_secret():
    session = AsyncMock()
    request = _request_with_body(b"{}")

    with patch("app.api.v1.webhooks.keycloak.settings") as mock_settings:
        mock_settings.keycloak_webhooks_enabled = True
        mock_settings.keycloak_webhook_secret = "secret"
        with pytest.raises(ValidationError):
            await post_keycloak_webhook(
                request=request,
                session=session,
                webhook_secret=None,
            )


@pytest.mark.asyncio
async def test_post_keycloak_webhook_processes_new_delivery():
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    secret = "local-kc-webhook-secret"
    payload = {
        "id": "evt-1",
        "type": "REGISTER",
        "userId": "kc-1",
        "details": {"email": "user@example.com"},
    }
    body = json.dumps(payload).encode()
    request = _request_with_body(body)

    with patch("app.api.v1.webhooks.keycloak.settings") as mock_settings:
        mock_settings.keycloak_webhooks_enabled = True
        mock_settings.keycloak_webhook_secret = secret
        with patch(
            "app.api.v1.webhooks.keycloak.accept_keycloak_webhook",
            new_callable=AsyncMock,
            return_value=True,
        ) as accept:
            with patch(
                "app.api.v1.webhooks.keycloak.apply_keycloak_webhook_event",
                new_callable=AsyncMock,
            ) as apply_event:
                response = await post_keycloak_webhook(
                    request=request,
                    session=session,
                    webhook_secret=secret,
                )

    assert response.status_code == 200
    accept.assert_awaited_once()
    apply_event.assert_awaited_once()
    session.commit.assert_awaited_once()


@pytest.mark.asyncio
async def test_post_keycloak_webhook_skips_duplicate():
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    secret = "local-kc-webhook-secret"
    payload = {"id": "evt-dup", "type": "REGISTER", "userId": "kc-1"}
    request = _request_with_body(json.dumps(payload).encode())

    with patch("app.api.v1.webhooks.keycloak.settings") as mock_settings:
        mock_settings.keycloak_webhooks_enabled = True
        mock_settings.keycloak_webhook_secret = secret
        with patch(
            "app.api.v1.webhooks.keycloak.accept_keycloak_webhook",
            new_callable=AsyncMock,
            return_value=False,
        ):
            with patch(
                "app.api.v1.webhooks.keycloak.apply_keycloak_webhook_event",
                new_callable=AsyncMock,
            ) as apply_event:
                response = await post_keycloak_webhook(
                    request=request,
                    session=session,
                    webhook_secret=secret,
                )

    assert response.status_code == 200
    apply_event.assert_not_awaited()


@pytest.mark.asyncio
async def test_post_keycloak_webhook_rolls_back_when_apply_raises():
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    secret = "local-kc-webhook-secret"
    payload = {
        "id": "evt-fail",
        "type": "REGISTER",
        "userId": "kc-1",
        "details": {"email": "user@example.com"},
    }
    request = _request_with_body(json.dumps(payload).encode())

    with patch("app.api.v1.webhooks.keycloak.settings") as mock_settings:
        mock_settings.keycloak_webhooks_enabled = True
        mock_settings.keycloak_webhook_secret = secret
        with patch(
            "app.api.v1.webhooks.keycloak.accept_keycloak_webhook",
            new_callable=AsyncMock,
            return_value=True,
        ):
            with patch(
                "app.api.v1.webhooks.keycloak.apply_keycloak_webhook_event",
                new_callable=AsyncMock,
                side_effect=ServiceUnavailableError(
                    message="Keycloak webhook payload missing user id",
                    error_code="keycloak_webhook_missing_user_id",
                ),
            ):
                with pytest.raises(ServiceUnavailableError):
                    await post_keycloak_webhook(
                        request=request,
                        session=session,
                        webhook_secret=secret,
                    )

    session.rollback.assert_awaited_once()
    session.commit.assert_not_awaited()


@pytest.mark.asyncio
async def test_post_keycloak_webhook_commits_on_non_retryable_provision_error():
    session = AsyncMock()
    session.commit = AsyncMock()
    session.rollback = AsyncMock()
    secret = "local-kc-webhook-secret"
    payload = {
        "id": "evt-perm",
        "type": "REGISTER",
        "userId": "kc-1",
        "details": {},
    }
    request = _request_with_body(json.dumps(payload).encode())

    with patch("app.api.v1.webhooks.keycloak.settings") as mock_settings:
        mock_settings.keycloak_webhooks_enabled = True
        mock_settings.keycloak_webhook_secret = secret
        with patch(
            "app.api.v1.webhooks.keycloak.accept_keycloak_webhook",
            new_callable=AsyncMock,
            return_value=True,
        ):
            with patch(
                "app.services.keycloak_webhooks.provision_user_from_keycloak",
                new_callable=AsyncMock,
                side_effect=UnauthorizedError(
                    "User not provisioned",
                    error_code="provision_email_required",
                ),
            ):
                response = await post_keycloak_webhook(
                    request=request,
                    session=session,
                    webhook_secret=secret,
                )

    assert response.status_code == 200
    session.commit.assert_awaited_once()
    session.rollback.assert_not_awaited()
