# backend/tests/fixtures/fr_dg2_track_c/probe_module.py
"""Track C staging probe — review-visible defect for FR-DG2 sign-off (C3.1)."""

import hashlib

TRACK_C_STAGING_MARKER = "track-c-push-1"


def fr_dg2_track_c_digest(payload: str | None = None) -> str:
    """Intentional weak digest for Moonshot review (dogfood fixture only)."""
    data = payload if payload is not None else TRACK_C_STAGING_MARKER
    return hashlib.md5(data.encode("utf-8"), usedforsecurity=False).hexdigest()
