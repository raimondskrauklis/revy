# backend/tests/unit/test_email.py
"""Email provider + dispatch helpers."""
from unittest.mock import patch

import pytest

from app.core.email import get_email_service, reset_email_service
from app.core.email.base import EmailMessage
from app.services.email_dispatch import (
    build_accept_invitation_url,
    deserialize_email_message,
    serialize_email_message,
)
from app.services.email_templates import build_workspace_invitation_email


@pytest.fixture(autouse=True)
def _reset_email_singleton():
    reset_email_service()
    yield
    reset_email_service()


@pytest.mark.asyncio
async def test_console_provider_sends_successfully():
    with patch("app.core.email.settings.email_provider", "console"):
        service = get_email_service()
        result = await service.send_email(
            EmailMessage(
                to_email="user@example.com",
                subject="Hello",
                html_body="<p>Hi</p>",
            )
        )
    assert result.success is True
    assert result.provider == "console"


def test_email_message_roundtrip():
    message = EmailMessage(
        to_email="a@b.com",
        subject="S",
        html_body="<p>x</p>",
        tags=["invite"],
    )
    restored = deserialize_email_message(serialize_email_message(message))
    assert restored.to_email == message.to_email
    assert restored.tags == message.tags


def test_build_workspace_invitation_email_contains_accept_url():
    message = build_workspace_invitation_email(
        to_email="invitee@example.com",
        inviter_name="Alex",
        workspace_name="Acme",
        accept_url="https://app.example.com/invite/accept?token=abc",
    )
    assert "Acme" in message.subject
    assert "token=abc" in message.html_body


def test_build_accept_invitation_url():
    with patch("app.services.email_dispatch.settings") as mock_settings:
        mock_settings.app_public_url = "https://app.example.com"
        url = build_accept_invitation_url("secret-token")
    assert url == "https://app.example.com/invite/accept?token=secret-token"
