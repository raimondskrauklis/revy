# backend/app/integrations/keycloak_webhook.py
"""Keycloak HTTP event listener verification — vymalo/keycloak-webhook 0.10.0-rc.1.

Listener: https://github.com/vymalo/keycloak-webhook (HTTP provider, KC 26).
Auth (vymalo): HTTP Basic via ``WEBHOOK_HTTP_AUTH_USERNAME`` / ``WEBHOOK_HTTP_AUTH_PASSWORD``.
Auth (Revy API): ``X-Webhook-Secret`` header **or** Basic password matching ``KEYCLOAK_WEBHOOK_SECRET``.

Sample user event payload (shape may vary by listener version):

```json
{
  "id": "evt-123",
  "type": "REGISTER",
  "userId": "kc-sub-uuid",
  "time": 1710000000000,
  "details": {
    "email": "user@example.com",
    "email_verified": "true"
  }
}
```
"""
from __future__ import annotations

import base64
import hmac


def verify_keycloak_webhook_secret(header: str | None, secret: str) -> bool:
    if not header or not secret:
        return False
    return hmac.compare_digest(header, secret)


def verify_keycloak_webhook_basic_auth(authorization: str | None, secret: str) -> bool:
    if not authorization or not secret:
        return False
    scheme, _, credentials = authorization.partition(" ")
    if scheme.lower() != "basic" or not credentials:
        return False
    try:
        decoded = base64.b64decode(credentials).decode("utf-8")
    except (ValueError, UnicodeDecodeError):
        return False
    _, _, password = decoded.partition(":")
    return hmac.compare_digest(password, secret)
