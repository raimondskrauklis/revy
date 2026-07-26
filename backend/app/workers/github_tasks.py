# backend/app/workers/github_tasks.py
"""GitHub webhook Celery tasks — github_events queue."""
from __future__ import annotations

import asyncio

from app.core.database import get_db_context
from app.core.logging import get_logger
from app.models.github_webhook_delivery import GitHubWebhookDeliveryORM
from app.services.github_installations import apply_installation_webhook_event
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(name="app.workers.github_tasks.process_github_event", bind=True, max_retries=3)
def process_github_event(self, delivery_id: str) -> None:
    async def _run() -> None:
        async with get_db_context() as session:
            delivery = await session.get(GitHubWebhookDeliveryORM, delivery_id)
            if delivery is None:
                raise RuntimeError("github_delivery_not_found")

            payload = delivery.payload_json
            event_type = delivery.event_type

            if event_type == "installation":
                installation = payload.get("installation")
                action = payload.get("action")
                if (
                    isinstance(installation, dict)
                    and isinstance(action, str)
                    and isinstance(installation.get("id"), int)
                ):
                    await apply_installation_webhook_event(
                        session,
                        github_installation_id=installation["id"],
                        action=action,
                    )
                return

            if event_type in {"push", "installation_repositories"}:
                logger.info(
                    "github_webhook_event_stub",
                    extra={
                        "delivery_id": delivery_id,
                        "event_type": event_type,
                        "installation_id": delivery.installation_id,
                    },
                )
                return

            logger.info(
                "github_webhook_event_unhandled",
                extra={"delivery_id": delivery_id, "event_type": event_type},
            )

    try:
        asyncio.run(_run())
    except Exception as exc:
        logger.error(
            "github_webhook_task_failed",
            extra={"delivery_id": delivery_id, "error": str(exc), "retries": self.request.retries},
        )
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=15 * (2**self.request.retries)) from exc
        raise
