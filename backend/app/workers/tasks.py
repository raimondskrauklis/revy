# backend/app/workers/tasks.py
"""Celery tasks — register with celery_app; see docs/backend/WORKERS.md."""
from __future__ import annotations

from app.workers.celery_app import celery_app


@celery_app.task(name="app.workers.tasks.send_notification", bind=True, max_retries=3)
def send_notification(self, *, user_id: str, template: str, payload: dict) -> None:
    """Example task — replace with outbox dispatcher in product phase."""
    _ = (self, user_id, template, payload)
