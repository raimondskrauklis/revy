# backend/app/workers/celery_app.py
"""Celery app — broker/backend from app.core.config (no localhost fallbacks)."""
from celery import Celery

from app.core.config import settings
from app.core.sentry import init_sentry

init_sentry()

celery_app = Celery(
    "app",
    broker=settings.celery_broker,
    backend=settings.celery_backend,
)
celery_app.conf.task_routes = {
    "app.workers.tasks.send_notification": {"queue": "notifications"},
    "app.workers.email_tasks.send_email": {"queue": "notifications"},
    "app.workers.tasks.heavy_job": {"queue": "heavy"},
    "app.workers.github_tasks.*": {"queue": "github_events"},
    "app.workers.repo_tasks.*": {"queue": "repo_sync"},
    "app.workers.index_tasks.*": {"queue": "indexing"},
    "app.workers.review_tasks.*": {"queue": "review"},
    "app.workers.reconcile_tasks.*": {"queue": "reconciliation"},
    "app.workers.judge_tasks.*": {"queue": "judge"},
    "app.workers.publish_tasks.*": {"queue": "github_publish"},
    "app.workers.maintenance_tasks.*": {"queue": "maintenance"},
}
celery_app.conf.task_default_queue = "default"

# Register task modules
from app.workers import email_tasks as _email_tasks  # noqa: F401
from app.workers import tasks as _tasks  # noqa: F401
