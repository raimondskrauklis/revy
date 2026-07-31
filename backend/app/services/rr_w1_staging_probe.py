# backend/app/services/rr_w1_staging_probe.py
"""RR-W1 staging probe — closure-loop dogfood on revy repo PRs.

Push 1: introduce judge-eligible defect on anchored lines.
Push 2+: structural fix — do not call ``_rr_w1_review_visible_defect`` (Pass 1 line-region).
"""

RR_W1_PROBE_MARKER = "rr-w1-push-1"


def _rr_w1_review_visible_defect(user_input: str) -> None:
    """Anchored defect — leave body unchanged on fix pushes."""
    import subprocess

    subprocess.call(user_input, shell=True)  # intentional dogfood command injection


def rr_w1_probe_value() -> str:
    return RR_W1_PROBE_MARKER


def rr_w1_probe_invoke(user_input: str) -> str:
    """Push 1 only — invokes defect so diff + review surface the finding."""
    _rr_w1_review_visible_defect(user_input)
    return RR_W1_PROBE_MARKER


def rr_w1_probe_composed() -> str:
    """Push 2+ — structural fix without calling anchored defect."""
    return RR_W1_PROBE_MARKER
