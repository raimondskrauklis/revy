# backend/app/workers/email_tasks.py
"""Email delivery tasks — notifications queue."""
from __future__ import annotations

import asyncio

from app.core.logging import get_logger
from app.services.email_dispatch import deliver_email_message, deserialize_email_message
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(name="app.workers.email_tasks.send_email", bind=True, max_retries=3)
def send_email_task(self, message_payload: dict) -> None:
    message = deserialize_email_message(message_payload)

    async def _run() -> None:
        result = await deliver_email_message(message)
        if not result.success:
            raise RuntimeError(result.error or "email_send_failed")

    try:
        asyncio.run(_run())
    except Exception as exc:
        countdown = 60 * (2 ** self.request.retries)
        logger.error(
            "email_task_failed",
            extra={
                "to": message.to_email,
                "retries": self.request.retries,
                "error": str(exc),
            },
        )
        raise self.retry(exc=exc, countdown=countdown) from exc
