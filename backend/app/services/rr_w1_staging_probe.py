# backend/app/services/rr_w1_staging_probe.py
"""RR-W1 staging probe — closure-loop dogfood on revy repo PRs.

Push 1: introduce judge-eligible defect on anchored lines.
Push 2: structural fix — stop calling defect (FR-CS4 pattern; re-report risk).
Push 3+: remove defect body (line-region fix) for addressed closure.
"""

RR_W1_PROBE_MARKER = "rr-w1-push-1"


def rr_w1_probe_value() -> str:
    return RR_W1_PROBE_MARKER


def rr_w1_probe_invoke(user_input: str) -> str:
    """Push 2+ — invoke path routes to composed (defect removed push 3+)."""
    _ = user_input
    return rr_w1_probe_composed()


def rr_w1_probe_composed() -> str:
    """Push 2+ — structural fix without command-injection defect."""
    return RR_W1_PROBE_MARKER
