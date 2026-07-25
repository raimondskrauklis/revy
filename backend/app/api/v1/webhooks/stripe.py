# backend/app/api/v1/webhooks/stripe.py
"""Stripe webhook — raw body signature verification and idempotent dispatch."""
from __future__ import annotations

from typing import Annotated

from fastapi import APIRouter, Depends, Header, Request, status
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.responses import Response

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import ServiceUnavailableError, ValidationError
from app.integrations.stripe_client import get_stripe_client
from app.services.billing import apply_subscription_event, try_record_webhook_event

router = APIRouter()


@router.post("/stripe", status_code=status.HTTP_200_OK)
async def post_stripe_webhook(
    request: Request,
    session: Annotated[AsyncSession, Depends(get_db)],
    stripe_signature: str | None = Header(default=None, alias="Stripe-Signature"),
) -> Response:
    if not settings.stripe_enabled:
        raise ServiceUnavailableError(
            message="Billing is not configured",
            error_code="billing_disabled",
        )
    if not stripe_signature:
        raise ValidationError(message="Missing Stripe-Signature header", field="Stripe-Signature")

    payload = await request.body()
    stripe_client = get_stripe_client()
    event = stripe_client.construct_webhook_event(payload, stripe_signature)

    is_new = await try_record_webhook_event(
        session,
        event_id=event["id"],
        event_type=event["type"],
    )
    if not is_new:
        await session.commit()
        return Response(status_code=status.HTTP_200_OK)

    await apply_subscription_event(session, event, stripe_client=stripe_client)
    await session.commit()
    return Response(status_code=status.HTTP_200_OK)
