# backend/app/integrations/github_webhook.py
"""GitHub webhook signature verification — product/revy/docs/WEBHOOKS.md."""
from __future__ import annotations

import hashlib
import hmac


def verify_github_signature(payload: bytes, signature: str | None, secret: str) -> bool:
    if not signature or not signature.startswith("sha256="):
        return False
    expected = hmac.new(secret.encode(), payload, hashlib.sha256).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
