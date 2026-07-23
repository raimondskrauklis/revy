# backend/app/core/email/__init__.py
"""Email provider factory — console (local) or mailgun (production)."""
from __future__ import annotations

from app.core.config import settings
from app.core.email.base import EmailMessage, EmailSendResult, EmailServiceBase
from app.core.logging import get_logger

logger = get_logger(__name__)

_email_service: EmailServiceBase | None = None

_SUPPORTED_PROVIDERS = frozenset({"console", "mailgun"})


def get_email_service() -> EmailServiceBase:
    global _email_service
    if _email_service is not None:
        return _email_service

    provider = settings.email_provider.strip().lower()
    if provider not in _SUPPORTED_PROVIDERS:
        raise ValueError(
            f"Unknown EMAIL_PROVIDER '{provider}'. Supported: {', '.join(sorted(_SUPPORTED_PROVIDERS))}"
        )

    if provider == "mailgun":
        from app.core.email.providers.mailgun import MailgunEmailService

        _email_service = MailgunEmailService()
    else:
        from app.core.email.providers.console import ConsoleEmailService

        _email_service = ConsoleEmailService()

    logger.info("email_service_initialized", extra={"provider": _email_service.provider_name})
    return _email_service


def reset_email_service() -> None:
    global _email_service
    _email_service = None


__all__ = [
    "EmailMessage",
    "EmailSendResult",
    "EmailServiceBase",
    "get_email_service",
    "reset_email_service",
]
