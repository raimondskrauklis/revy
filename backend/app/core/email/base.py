# backend/app/core/email/base.py
"""Vendor-agnostic email interface — implementations in providers/."""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class EmailSendResult:
    success: bool
    provider: str
    message_id: str | None = None
    response_data: dict = field(default_factory=dict)
    error: str | None = None


@dataclass
class EmailMessage:
    to_email: str
    subject: str
    html_body: str
    text_body: str | None = None
    from_email: str | None = None
    from_name: str | None = None
    reply_to: str | None = None
    cc: list[str] | None = None
    bcc: list[str] | None = None
    tags: list[str] | None = None
    metadata: dict[str, str] | None = None


class EmailServiceBase(ABC):
    @property
    @abstractmethod
    def provider_name(self) -> str:
        pass

    @abstractmethod
    async def send_email(self, message: EmailMessage) -> EmailSendResult:
        pass

    async def send_raw_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str | None = None,
    ) -> EmailSendResult:
        return await self.send_email(
            EmailMessage(
                to_email=to_email,
                subject=subject,
                html_body=html_body,
                text_body=text_body,
            )
        )

    @abstractmethod
    async def health_check(self) -> bool:
        pass
