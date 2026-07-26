# backend/app/services/keycloak_webhooks.py
"""Keycloak identity webhook dispatch — USER_PROVISIONING P1."""
from __future__ import annotations

import hashlib
import json
from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.keycloak_webhook_delivery import KeycloakWebhookDeliveryORM
from app.services.keycloak_provisioning import (
    apply_keycloak_user_deleted,
    apply_keycloak_user_disabled,
    provision_user_from_keycloak,
)

logger = get_logger(__name__)

_UNIQUE_VIOLATION_PG_CODE = "23505"

PROVISION_EVENTS = frozenset({
    "REGISTER",
    "IDENTITY_PROVIDER_FIRST_LOGIN",
    "IDENTITY_PROVIDER_LINK",
})

UPDATE_EVENTS = frozenset({
    "UPDATE_PROFILE",
    "UPDATE_EMAIL",
})

DISABLE_EVENTS = frozenset({
    "DELETE_ACCOUNT",
})

IGNORED_EVENTS = frozenset({
    "LOGIN",
    "LOGOUT",
    "CODE_TO_TOKEN",
    "REFRESH_TOKEN",
})


def _is_unique_violation(exc: IntegrityError) -> bool:
    orig = exc.orig
    return orig is not None and getattr(orig, "pgcode", None) == _UNIQUE_VIOLATION_PG_CODE


def _parse_bool(value: object, *, default: bool = False) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return default
    return str(value).strip().lower() in {"true", "1", "yes"}


def normalize_event_type(payload: dict[str, Any], header_event: str | None) -> str:
    raw = payload.get("type") or payload.get("eventType") or header_event or ""
    return str(raw).strip().upper()


def delivery_id_from_payload(event_type: str, payload: dict[str, Any]) -> str:
    for key in ("id", "eventId", "event_id"):
        value = payload.get(key)
        if value:
            return str(value)
    user_id = extract_user_sub(payload) or ""
    time_value = payload.get("time") or payload.get("timestamp") or ""
    digest = hashlib.sha256(f"{event_type}:{user_id}:{time_value}".encode()).hexdigest()
    return digest


def extract_user_sub(payload: dict[str, Any]) -> str | None:
    for key in ("userId", "user_id", "sub"):
        value = payload.get(key)
        if value:
            return str(value)
    details = payload.get("details")
    if isinstance(details, dict):
        for key in ("userId", "user_id", "sub"):
            value = details.get(key)
            if value:
                return str(value)
    return None


def extract_email(payload: dict[str, Any]) -> str | None:
    details = payload.get("details")
    if isinstance(details, dict):
        email = details.get("email")
        if email:
            return str(email)
    email = payload.get("email")
    return str(email) if email else None


def extract_email_verified(payload: dict[str, Any], *, event_type: str) -> bool:
    details = payload.get("details")
    if isinstance(details, dict) and "email_verified" in details:
        return _parse_bool(details.get("email_verified"))
    return event_type in PROVISION_EVENTS


def extract_enabled(payload: dict[str, Any]) -> bool | None:
    details = payload.get("details")
    if isinstance(details, dict) and "enabled" in details:
        return _parse_bool(details.get("enabled"))
    if "enabled" in payload:
        return _parse_bool(payload.get("enabled"))
    return None


def extract_display_name(payload: dict[str, Any]) -> str | None:
    details = payload.get("details")
    if not isinstance(details, dict):
        return None
    first = str(details.get("first_name") or details.get("given_name") or "").strip()
    last = str(details.get("last_name") or details.get("family_name") or "").strip()
    name = " ".join(part for part in (first, last) if part)
    return name or None


async def try_record_delivery(
    session: AsyncSession,
    *,
    delivery_id: str,
    event_type: str,
    payload: dict[str, Any],
) -> bool:
    existing = await session.get(KeycloakWebhookDeliveryORM, delivery_id)
    if existing is not None:
        return False

    session.add(
        KeycloakWebhookDeliveryORM(
            delivery_id=delivery_id,
            event_type=event_type,
            payload_json=payload,
        )
    )
    try:
        async with session.begin_nested():
            await session.flush()
    except IntegrityError as exc:
        if not _is_unique_violation(exc):
            raise
        logger.info(
            "keycloak_webhook_duplicate_delivery",
            extra={"delivery_id": delivery_id},
        )
        return False
    return True


async def accept_keycloak_webhook(
    session: AsyncSession,
    *,
    delivery_id: str,
    event_type: str,
    payload: dict[str, Any],
) -> bool:
    if event_type in IGNORED_EVENTS:
        logger.info(
            "keycloak_webhook_ignored_event",
            extra={"event_type": event_type, "delivery_id": delivery_id},
        )
        return False
    return await try_record_delivery(
        session,
        delivery_id=delivery_id,
        event_type=event_type,
        payload=payload,
    )


async def apply_keycloak_webhook_event(
    session: AsyncSession,
    *,
    event_type: str,
    payload: dict[str, Any],
) -> bool:
    sub = extract_user_sub(payload)
    if sub is None:
        logger.warning(
            "keycloak_webhook_missing_user_id",
            extra={"event_type": event_type},
        )
        return False

    if event_type in PROVISION_EVENTS | UPDATE_EVENTS:
        email = extract_email(payload)
        await provision_user_from_keycloak(
            session,
            sub=sub,
            email=email,
            email_verified=extract_email_verified(payload, event_type=event_type),
            display_name=extract_display_name(payload),
        )
        return True

    if event_type in DISABLE_EVENTS:
        await apply_keycloak_user_deleted(session, sub=sub)
        return True

    enabled = extract_enabled(payload)
    if enabled is not None and event_type.startswith("ADMIN"):
        await apply_keycloak_user_disabled(session, sub=sub, enabled=enabled)
        return True

    logger.info(
        "keycloak_webhook_unhandled_event",
        extra={"event_type": event_type},
    )
    return False


def parse_json_payload(body: bytes) -> dict[str, Any]:
    data = json.loads(body.decode())
    if not isinstance(data, dict):
        raise ValueError("payload must be a JSON object")
    return data
