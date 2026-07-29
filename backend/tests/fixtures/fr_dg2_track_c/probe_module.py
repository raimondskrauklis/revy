# backend/tests/fixtures/fr_dg2_track_c/probe_module.py
"""Track C staging probe — review-visible defect for FR-DG2 sign-off (C3.1)."""

import hashlib


def fr_dg2_track_c_digest(payload: str) -> str:
    """Intentional weak digest for Moonshot review (dogfood fixture only)."""
    return hashlib.md5(payload.encode("utf-8"), usedforsecurity=False).hexdigest()
