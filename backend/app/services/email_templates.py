# backend/app/services/email_templates.py
"""Transactional email bodies — product copy lives here (EN first; i18n later)."""
from __future__ import annotations

from app.core.email.base import EmailMessage


def build_workspace_invitation_email(
    *,
    to_email: str,
    inviter_name: str,
    workspace_name: str,
    accept_url: str,
    app_name: str = "App",
) -> EmailMessage:
    subject = f"{inviter_name} invited you to {workspace_name}"
    text_body = (
        f"{inviter_name} invited you to join {workspace_name} on {app_name}.\n\n"
        f"Accept invitation: {accept_url}\n\n"
        "If you did not expect this email, you can ignore it."
    )
    html_body = f"""
<p>{inviter_name} invited you to join <strong>{workspace_name}</strong> on {app_name}.</p>
<p><a href="{accept_url}">Accept invitation</a></p>
<p style="color:#64748B;font-size:12px">If you did not expect this email, you can ignore it.</p>
""".strip()
    return EmailMessage(
        to_email=to_email,
        subject=subject,
        html_body=html_body,
        text_body=text_body,
        tags=["workspace_invitation"],
        metadata={"template": "workspace_invitation"},
    )
