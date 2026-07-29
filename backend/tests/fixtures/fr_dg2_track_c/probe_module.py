# backend/tests/fixtures/fr_dg2_track_c/probe_module.py
"""Track C staging probe — review-visible defect for FR-DG2 sign-off."""

import hashlib


def fr_dg2_track_c_digest(payload: str) -> str:
    """Intentional weak digest for Moonshot review (dogfood only)."""
    return hashlib.md5(payload.encode("utf-8")).hexdigest()
