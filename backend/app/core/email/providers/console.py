# backend/app/core/email/providers/console.py
"""Local/dev provider — logs email metadata, never calls external APIs."""
from __future__ import annotations

from app.core.email.base import EmailMessage, EmailSendResult, EmailServiceBase
from app.core.logging import get_logger

logger = get_logger(__name__)


class ConsoleEmailService(EmailServiceBase):
    @property
    def provider_name(self) -> str:
        return "console"

    async def send_email(self, message: EmailMessage) -> EmailSendResult:
        logger.info(
            "email_console_send",
            extra={
                "to": message.to_email,
                "subject": message.subject[:120],
                "tags": ",".join(message.tags or []),
                "provider": self.provider_name,
            },
        )
        return EmailSendResult(
            success=True,
            provider=self.provider_name,
            message_id="console-local",
        )

    async def health_check(self) -> bool:
        return True
