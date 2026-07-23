# backend/app/services/email_dispatch.py
"""Enqueue or deliver transactional email — never call Mailgun from route handlers."""
from __future__ import annotations

from dataclasses import asdict, fields

from app.core.config import settings
from app.core.email import get_email_service
from app.core.email.base import EmailMessage, EmailSendResult
from app.core.logging import get_logger
from app.services.email_templates import build_workspace_invitation_email

logger = get_logger(__name__)


def serialize_email_message(message: EmailMessage) -> dict:
    return asdict(message)


def deserialize_email_message(payload: dict) -> EmailMessage:
    allowed = {field.name for field in fields(EmailMessage)}
    return EmailMessage(**{key: payload[key] for key in allowed if key in payload})


def build_accept_invitation_url(token: str) -> str:
    base = (settings.app_public_url or "http://localhost:5173").rstrip("/")
    return f"{base}/invite/accept?token={token}"


async def deliver_email_message(message: EmailMessage) -> EmailSendResult:
    service = get_email_service()
    result = await service.send_email(message)
    if not result.success:
        logger.error(
            "email_delivery_failed",
            extra={
                "to": message.to_email,
                "provider": result.provider,
                "error": result.error,
            },
        )
    return result


def enqueue_email_message(message: EmailMessage) -> None:
    """Fire-and-forget via Celery notifications queue (WORKERS.md)."""
    from app.workers.email_tasks import send_email_task

    send_email_task.delay(serialize_email_message(message))


def enqueue_workspace_invitation_email(
    *,
    to_email: str,
    inviter_name: str,
    workspace_name: str,
    accept_token: str,
) -> None:
    message = build_workspace_invitation_email(
        to_email=to_email,
        inviter_name=inviter_name,
        workspace_name=workspace_name,
        accept_url=build_accept_invitation_url(accept_token),
        app_name=settings.app_name,
    )
    enqueue_email_message(message)
