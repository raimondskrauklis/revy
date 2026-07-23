# backend/app/core/email/providers/mailgun.py
"""Mailgun HTTP API provider — production transactional email."""
from __future__ import annotations

import httpx

from app.core.config import settings
from app.core.email.base import EmailMessage, EmailSendResult, EmailServiceBase
from app.core.logging import get_logger

logger = get_logger(__name__)


class MailgunEmailService(EmailServiceBase):
    def __init__(self) -> None:
        self.api_key = settings.mailgun_api_key
        self.domain = settings.mailgun_domain
        self.region = (settings.mailgun_region or "eu").lower()
        self.from_email = settings.email_from
        self.from_name = settings.email_from_name
        self.base_url = (
            "https://api.eu.mailgun.net/v3"
            if self.region == "eu"
            else "https://api.mailgun.net/v3"
        )

    @property
    def provider_name(self) -> str:
        return "mailgun"

    def _build_from_address(self, message: EmailMessage) -> str:
        from_email = message.from_email or self.from_email
        from_name = message.from_name or self.from_name
        if not from_email:
            return ""
        if from_name:
            return f"{from_name} <{from_email}>"
        return from_email

    async def send_email(self, message: EmailMessage) -> EmailSendResult:
        if not self.api_key or not self.domain or not self.from_email:
            logger.error(
                "mailgun_not_configured",
                extra={"operation": "send_email", "provider": self.provider_name},
            )
            return EmailSendResult(
                success=False,
                provider=self.provider_name,
                error="Mailgun not configured",
            )

        data: dict[str, str | list[str]] = {
            "from": self._build_from_address(message),
            "to": message.to_email,
            "subject": message.subject,
            "html": message.html_body,
        }
        if message.text_body:
            data["text"] = message.text_body
        if message.reply_to:
            data["h:Reply-To"] = message.reply_to
        if message.cc:
            data["cc"] = ",".join(message.cc)
        if message.bcc:
            data["bcc"] = ",".join(message.bcc)
        if message.tags:
            data["o:tag"] = message.tags
        if message.metadata:
            for key, value in message.metadata.items():
                data[f"v:{key}"] = str(value)

        async with httpx.AsyncClient(timeout=15.0) as client:
            try:
                response = await client.post(
                    f"{self.base_url}/{self.domain}/messages",
                    auth=("api", self.api_key),
                    data=data,
                )
                response_data = response.json() if response.content else {}
                if response.is_success:
                    message_id = str(response_data.get("id", "")).strip("<>")
                    logger.info(
                        "mailgun_send_ok",
                        extra={
                            "to": message.to_email,
                            "message_id": message_id,
                            "provider": self.provider_name,
                        },
                    )
                    return EmailSendResult(
                        success=True,
                        provider=self.provider_name,
                        message_id=message_id,
                        response_data=response_data,
                    )

                error_msg = response_data.get("message", response.text)
                logger.error(
                    "mailgun_send_failed",
                    extra={
                        "status_code": response.status_code,
                        "error": str(error_msg)[:200],
                        "provider": self.provider_name,
                    },
                )
                return EmailSendResult(
                    success=False,
                    provider=self.provider_name,
                    response_data=response_data,
                    error=f"HTTP {response.status_code}: {error_msg}",
                )
            except httpx.TimeoutException:
                logger.error("mailgun_timeout", extra={"provider": self.provider_name})
                return EmailSendResult(
                    success=False,
                    provider=self.provider_name,
                    error="Request timeout",
                )
            except httpx.HTTPError as exc:
                logger.error(
                    "mailgun_http_error",
                    extra={"error": str(exc), "provider": self.provider_name},
                )
                return EmailSendResult(
                    success=False,
                    provider=self.provider_name,
                    error=str(exc),
                )

    async def health_check(self) -> bool:
        if not self.api_key or not self.domain:
            return False
        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.get(
                    f"{self.base_url}/domains/{self.domain}",
                    auth=("api", self.api_key),
                )
                return response.is_success
            except httpx.HTTPError:
                return False
