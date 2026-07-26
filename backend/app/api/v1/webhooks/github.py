# backend/app/api/v1/webhooks/github.py
"""GitHub App webhook — raw body HMAC verification and idempotent dispatch."""
from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import ServiceUnavailableError, ValidationError
from app.integrations.github_webhook import verify_github_signature
from app.services.github_webhooks import accept_github_webhook, enqueue_github_event

router = APIRouter()


@router.post("/github", status_code=status.HTTP_200_OK)
async def post_github_webhook(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
    github_signature: str | None = Header(default=None, alias="X-Hub-Signature-256"),
    github_event: str | None = Header(default=None, alias="X-GitHub-Event"),
    github_delivery: str | None = Header(default=None, alias="X-GitHub-Delivery"),
) -> Response:
    if not settings.github_webhooks_enabled:
        raise ServiceUnavailableError(
            message="GitHub webhooks are not configured",
            error_code="github_webhooks_disabled",
        )
    if not github_signature:
        raise ValidationError(
            message="Missing X-Hub-Signature-256 header",
            field="X-Hub-Signature-256",
        )
    if not github_event:
        raise ValidationError(message="Missing X-GitHub-Event header", field="X-GitHub-Event")
    if not github_delivery:
        raise ValidationError(
            message="Missing X-GitHub-Delivery header",
            field="X-GitHub-Delivery",
        )

    payload_bytes = await request.body()
    secret = settings.github_webhook_secret or ""
    if not verify_github_signature(payload_bytes, github_signature, secret):
        raise ValidationError(
            message="Invalid GitHub webhook signature",
            field="X-Hub-Signature-256",
        )

    try:
        payload = json.loads(payload_bytes)
    except json.JSONDecodeError as exc:
        raise ValidationError(message="Invalid JSON payload", field="body") from exc

    if not isinstance(payload, dict):
        raise ValidationError(message="Webhook payload must be a JSON object", field="body")

    accepted = await accept_github_webhook(
        session,
        delivery_id=github_delivery,
        event_type=github_event,
        payload=payload,
    )
    await session.commit()
    if accepted:
        enqueue_github_event(github_delivery)
    return Response(status_code=status.HTTP_200_OK)
