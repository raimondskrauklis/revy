# backend/app/integrations/stripe_client.py
"""Stripe SDK wrapper — real client when enabled, null object otherwise."""
from __future__ import annotations

from typing import Any, Protocol

import stripe

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError


class StripeClientProtocol(Protocol):
    def create_customer(
        self,
        *,
        email: str,
        name: str,
        metadata: dict[str, str],
    ) -> str: ...

    def create_checkout_session(
        self,
        *,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        metadata: dict[str, str],
    ) -> str: ...

    def create_portal_session(self, *, customer_id: str, return_url: str) -> str: ...

    def construct_webhook_event(self, payload: bytes, signature: str) -> Any: ...


class StripeClient:
    def __init__(self) -> None:
        stripe.api_key = settings.stripe_secret_key

    def create_customer(
        self,
        *,
        email: str,
        name: str,
        metadata: dict[str, str],
    ) -> str:
        customer = stripe.Customer.create(email=email, name=name, metadata=metadata)
        return customer.id

    def create_checkout_session(
        self,
        *,
        customer_id: str,
        price_id: str,
        success_url: str,
        cancel_url: str,
        metadata: dict[str, str],
    ) -> str:
        session = stripe.checkout.Session.create(
            mode="subscription",
            customer=customer_id,
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            metadata=metadata,
            subscription_data={"metadata": metadata},
        )
        return session.url or ""

    def create_portal_session(self, *, customer_id: str, return_url: str) -> str:
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=return_url,
        )
        return session.url

    def construct_webhook_event(self, payload: bytes, signature: str) -> Any:
        return stripe.Webhook.construct_event(
            payload,
            signature,
            settings.stripe_webhook_secret or "",
        )


class NullStripeClient:
    def _disabled(self) -> None:
        raise ServiceUnavailableError(
            message="Billing is not configured",
            error_code="billing_disabled",
        )

    def create_customer(self, **_: Any) -> str:
        self._disabled()
        raise AssertionError("unreachable")

    def create_checkout_session(self, **_: Any) -> str:
        self._disabled()
        raise AssertionError("unreachable")

    def create_portal_session(self, **_: Any) -> str:
        self._disabled()
        raise AssertionError("unreachable")

    def construct_webhook_event(self, **_: Any) -> Any:
        self._disabled()
        raise AssertionError("unreachable")


def get_stripe_client() -> StripeClientProtocol:
    if settings.stripe_enabled:
        return StripeClient()
    return NullStripeClient()
