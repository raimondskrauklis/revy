# backend/app/services/github_webhooks.py
"""GitHub webhook ingest — delivery dedupe and async dispatch."""
from __future__ import annotations

from typing import Any

from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import get_logger
from app.models.github_webhook_delivery import GitHubWebhookDeliveryORM

logger = get_logger(__name__)

SUPPORTED_EVENTS = frozenset({
    "installation",
    "installation_repositories",
    "push",
    "pull_request",
    "pull_request_review",
})


def extract_installation_id(payload: dict[str, Any]) -> int | None:
    installation = payload.get("installation")
    if isinstance(installation, dict):
        raw_id = installation.get("id")
        if isinstance(raw_id, int):
            return raw_id
    return None


async def try_record_delivery(
    session: AsyncSession,
    *,
    delivery_id: str,
    event_type: str,
    installation_id: int | None,
    payload: dict[str, Any],
) -> bool:
    existing = await session.get(GitHubWebhookDeliveryORM, delivery_id)
    if existing is not None:
        return False

    session.add(
        GitHubWebhookDeliveryORM(
            delivery_id=delivery_id,
            event_type=event_type,
            installation_id=installation_id,
            payload_json=payload,
        )
    )
    try:
        await session.flush()
    except IntegrityError:
        await session.rollback()
        return False
    return True


def enqueue_github_event(delivery_id: str) -> None:
    from app.workers.github_tasks import process_github_event

    process_github_event.delay(delivery_id)


async def accept_github_webhook(
    session: AsyncSession,
    *,
    delivery_id: str,
    event_type: str,
    payload: dict[str, Any],
) -> bool:
    if event_type not in SUPPORTED_EVENTS:
        logger.info(
            "github_webhook_ignored_event",
            extra={"event_type": event_type, "delivery_id": delivery_id},
        )
        return False

    installation_id = extract_installation_id(payload)
    is_new = await try_record_delivery(
        session,
        delivery_id=delivery_id,
        event_type=event_type,
        installation_id=installation_id,
        payload=payload,
    )
    return is_new
