# backend/app/services/rr_w1_staging_probe.py
"""RR-W1 staging probe — closure-loop dogfood marker (final / safe state).

Dogfood protocol completed on PR #80: defect introduced, fixed, and removed.
This module intentionally exposes only a stable marker for import smoke tests.
"""

RR_W1_PROBE_MARKER = "rr-w1-push-5"


def rr_w1_probe_value() -> str:
    return RR_W1_PROBE_MARKER


def rr_w1_probe_invoke(user_input: str) -> str:
    """Return composed probe value (invoke path retained for import stability)."""
    _ = user_input
    return rr_w1_probe_composed()


def rr_w1_probe_composed() -> str:
    """Return the stable RR-W1 dogfood marker."""
    return RR_W1_PROBE_MARKER
