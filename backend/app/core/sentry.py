# backend/app/core/sentry.py
"""Centralized Sentry initialization — FastAPI + Celery share one module."""

from __future__ import annotations

import os

import sentry_sdk
from sentry_sdk.integrations.celery import CeleryIntegration
from sentry_sdk.integrations.fastapi import FastApiIntegration
from sentry_sdk.integrations.logging import LoggingIntegration

from app.core.config import settings


def should_capture_sentry() -> bool:
    if not settings.sentry_dsn:
        return False
    if settings.environment == "test" and not settings.sentry_enable_in_test:
        return False
    return True


def init_sentry() -> None:
    """Initialize Sentry once per process. No-op when DSN is unset."""
    if not should_capture_sentry():
        return

    sentry_release = os.getenv("SENTRY_RELEASE") or settings.app_version

    sentry_sdk.init(
        dsn=settings.sentry_dsn,
        environment=settings.environment,
        release=sentry_release,
        send_default_pii=settings.sentry_send_default_pii,
        enable_logs=True,
        traces_sample_rate=(
            settings.sentry_traces_sample_rate_debug
            if settings.environment == "development"
            else settings.sentry_traces_sample_rate_prod
        ),
        integrations=[
            FastApiIntegration(),
            CeleryIntegration(),
            LoggingIntegration(
                level="INFO",
                event_level="ERROR",
            ),
        ],
    )


def capture_exception(exc: BaseException) -> None:
    """Capture to Sentry when DSN is configured (respects test env gate)."""
    if not should_capture_sentry():
        return
    sentry_sdk.capture_exception(exc)
