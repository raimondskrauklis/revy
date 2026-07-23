# backend/app/core/security.py
"""App-wide secret-derived helpers — SECRET_KEY from settings (CONFIG.md)."""
from __future__ import annotations

import hashlib

from app.core.config import settings


def app_secret_fingerprint(*, purpose: str) -> str:
    """Stable short prefix for Redis namespaces (one-way, not reversible)."""
    material = f"{purpose}:{settings.secret_key}".encode()
    return hashlib.sha256(material).hexdigest()[:16]
