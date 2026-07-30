# backend/app/services/fr_cs4_staging_probe.py
"""FR-CS4 staging probe — structural fix without line touch (D1.1).

Attempt 6 (D1-O12): judge-eligible security defect on anchored lines. Push 2
removes ``_fr_cs4_structural_root`` and stops invoking the defect — **do not edit**
``_fr_cs4_review_visible_defect`` body (Pass 1a line-region guard).
"""

FR_CS4_PROBE_MARKER = "fr-cs4-push-1"


def _fr_cs4_review_visible_defect(user_input: str) -> None:
    """Anchored defect — leave this function body unchanged on push 2."""
    import subprocess

    subprocess.call(user_input, shell=True)  # intentional dogfood command injection


def fr_cs4_probe_value() -> str:
    """Stable import hook for unit tests."""
    return FR_CS4_PROBE_MARKER


def _fr_cs4_structural_root() -> bool:
    """Push-2 removal target — outside anchored defect lines."""
    return True


def fr_cs4_probe_composed(user_input: str = "echo fr-cs4") -> str:
    """Push 1: root gates defect invocation. Push 2: drop root + defect call."""
    if _fr_cs4_structural_root():
        _fr_cs4_review_visible_defect(user_input)
    return FR_CS4_PROBE_MARKER
