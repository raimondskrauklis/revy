# backend/app/services/fr_cs4_staging_probe.py
"""FR-CS4 staging probe — structural fix without line touch (D1.2 push 2).

Push 2: structural root removed; defect no longer invoked. **Do not edit**
``_fr_cs4_review_visible_defect`` body (Pass 1a line-region guard; anchored lines 12–16).
"""

FR_CS4_PROBE_MARKER = "fr-cs4-push-1"


def _fr_cs4_review_visible_defect(user_input: str) -> None:
    """Anchored defect — leave this function body unchanged on push 2."""
    import subprocess

    subprocess.call(user_input, shell=True)  # intentional dogfood command injection


def fr_cs4_probe_value() -> str:
    """Stable import hook for unit tests."""
    return FR_CS4_PROBE_MARKER


def fr_cs4_probe_composed() -> str:
    """Push 2: no defect invocation — structural fix outside anchored lines."""
    return FR_CS4_PROBE_MARKER
