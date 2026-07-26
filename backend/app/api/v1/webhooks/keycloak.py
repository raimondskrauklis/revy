# backend/app/api/v1/webhooks/keycloak.py
"""Keycloak identity webhook — shared-secret verification and idempotent dispatch."""
from __future__ import annotations

import json
from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import ServiceUnavailableError, ValidationError
from app.integrations.keycloak_webhook import (
    verify_keycloak_webhook_basic_auth,
    verify_keycloak_webhook_secret,
)
from app.services.keycloak_webhooks import (
    accept_keycloak_webhook,
    apply_keycloak_webhook_event,
    delivery_id_from_payload,
    normalize_event_type,
)

router = APIRouter()


@router.post("/keycloak", status_code=status.HTTP_200_OK)
async def post_keycloak_webhook(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
    webhook_secret: str | None = Header(default=None, alias="X-Webhook-Secret"),
    keycloak_event: str | None = Header(default=None, alias="X-Keycloak-Event"),
) -> Response:
    if not settings.keycloak_webhooks_enabled:
        raise ServiceUnavailableError(
            message="Keycloak webhooks are not configured",
            error_code="keycloak_webhooks_disabled",
        )
    secret = settings.keycloak_webhook_secret or ""
    authorized = verify_keycloak_webhook_secret(webhook_secret, secret)
    if not authorized:
        authorized = verify_keycloak_webhook_basic_auth(
            request.headers.get("authorization"),
            secret,
        )
    if not authorized:
        raise ValidationError(
            message="Invalid Keycloak webhook secret",
            field="X-Webhook-Secret",
        )

    body = await request.body()
    try:
        payload = json.loads(body.decode())
    except json.JSONDecodeError as exc:
        raise ValidationError(message="Invalid JSON payload") from exc
    if not isinstance(payload, dict):
        raise ValidationError(message="Webhook payload must be a JSON object")

    event_type = normalize_event_type(payload, keycloak_event)
    delivery_id = delivery_id_from_payload(event_type, payload)

    accepted = await accept_keycloak_webhook(
        session,
        delivery_id=delivery_id,
        event_type=event_type,
        payload=payload,
    )
    try:
        if accepted:
            await apply_keycloak_webhook_event(session, event_type=event_type, payload=payload)
        await session.commit()
    except Exception:
        await session.rollback()
        raise
    return Response(status_code=status.HTTP_200_OK)
