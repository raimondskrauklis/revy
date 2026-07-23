# backend/app/core/email/providers/__init__.py
from app.core.email.providers.console import ConsoleEmailService
from app.core.email.providers.mailgun import MailgunEmailService

__all__ = ["ConsoleEmailService", "MailgunEmailService"]
