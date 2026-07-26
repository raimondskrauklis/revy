# backend/tests/unit/test_github_webhook.py
"""GitHub webhook handler — signature, idempotency, dispatch."""
import hashlib
import hmac
import json
from unittest.mock import AsyncMock, patch

import pytest
from starlette.requests import Request

from app.api.v1.webhooks.github import post_github_webhook
from app.core.exceptions import ServiceUnavailableError, ValidationError


def _request_with_body(body: bytes) -> Request:
    scope = {
        "type": "http",
        "method": "POST",
        "path": "/api/v1/webhooks/github",
        "headers": [],
    }

    async def receive():
        return {"type": "http.request", "body": body, "more_body": False}

    return Request(scope, receive)


def _signature(body: bytes, secret: str) -> str:
    digest = hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()
    return f"sha256={digest}"


@pytest.mark.asyncio
async def test_post_github_webhook_disabled_raises():
    session = AsyncMock()
    request = _request_with_body(b"{}")

    with patch("app.api.v1.webhooks.github.settings") as mock_settings:
        mock_settings.github_webhooks_enabled = False
        with pytest.raises(ServiceUnavailableError) as exc:
            await post_github_webhook(
                request=request,
                session=session,
                github_signature="sig",
                github_event="installation",
                github_delivery="delivery-1",
            )

    assert exc.value.error_code == "github_webhooks_disabled"


@pytest.mark.asyncio
async def test_post_github_webhook_requires_signature():
    session = AsyncMock()
    request = _request_with_body(b"{}")

    with patch("app.api.v1.webhooks.github.settings") as mock_settings:
        mock_settings.github_webhooks_enabled = True
        with pytest.raises(ValidationError):
            await post_github_webhook(
                request=request,
                session=session,
                github_signature=None,
                github_event="installation",
                github_delivery="delivery-1",
            )


@pytest.mark.asyncio
async def test_post_github_webhook_processes_new_delivery():
    session = AsyncMock()
    session.commit = AsyncMock()
    secret = "local-webhook-secret"
    payload = {
        "action": "created",
        "installation": {"id": 12345},
    }
    body = json.dumps(payload).encode()
    request = _request_with_body(body)

    with patch("app.api.v1.webhooks.github.settings") as mock_settings:
        mock_settings.github_webhooks_enabled = True
        mock_settings.github_webhook_secret = secret
        with patch(
            "app.api.v1.webhooks.github.accept_github_webhook",
            AsyncMock(return_value=True),
        ) as accept_mock:
            with patch("app.api.v1.webhooks.github.enqueue_github_event") as enqueue_mock:
                response = await post_github_webhook(
                    request=request,
                    session=session,
                    github_signature=_signature(body, secret),
                    github_event="installation",
                    github_delivery="delivery-new",
                )

    assert response.status_code == 200
    accept_mock.assert_awaited_once()
    session.commit.assert_awaited_once()
    enqueue_mock.assert_called_once_with("delivery-new")


@pytest.mark.asyncio
async def test_post_github_webhook_duplicate_skips_enqueue():
    session = AsyncMock()
    session.commit = AsyncMock()
    secret = "local-webhook-secret"
    payload = {"installation": {"id": 12345}}
    body = json.dumps(payload).encode()
    request = _request_with_body(body)

    with patch("app.api.v1.webhooks.github.settings") as mock_settings:
        mock_settings.github_webhooks_enabled = True
        mock_settings.github_webhook_secret = secret
        with patch(
            "app.api.v1.webhooks.github.accept_github_webhook",
            AsyncMock(return_value=False),
        ):
            with patch("app.api.v1.webhooks.github.enqueue_github_event") as enqueue_mock:
                response = await post_github_webhook(
                    request=request,
                    session=session,
                    github_signature=_signature(body, secret),
                    github_event="installation",
                    github_delivery="delivery-dup",
                )

    assert response.status_code == 200
    session.commit.assert_awaited_once()
    enqueue_mock.assert_not_called()


@pytest.mark.asyncio
async def test_post_github_webhook_rejects_bad_signature():
    session = AsyncMock()
    body = b'{"installation":{"id":1}}'
    request = _request_with_body(body)

    with patch("app.api.v1.webhooks.github.settings") as mock_settings:
        mock_settings.github_webhooks_enabled = True
        mock_settings.github_webhook_secret = "secret"
        with pytest.raises(ValidationError):
            await post_github_webhook(
                request=request,
                session=session,
                github_signature="sha256=invalid",
                github_event="installation",
                github_delivery="delivery-bad",
            )
