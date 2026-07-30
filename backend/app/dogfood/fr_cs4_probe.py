# backend/app/dogfood/fr_cs4_probe.py
"""FR-CS4 staging probe — structural fix without line touch (D1.1).

Attempt 3 (D1-O4): non-test path + ``eval`` anchored defect. Push 2 removes
``_fr_cs4_structural_root`` and stops invoking the defect — **do not edit** the
defect function body (Pass 1a line-region guard).
"""

FR_CS4_PROBE_MARKER = "fr-cs4-push-1"


def _fr_cs4_review_visible_defect(expression: str) -> int:
    """Anchored defect — leave this function body unchanged on push 2."""
    return int(eval(expression))  # intentional dogfood defect


def fr_cs4_probe_value() -> str:
    """Stable import hook for unit tests."""
    return FR_CS4_PROBE_MARKER


def _fr_cs4_structural_root() -> bool:
    """Push-2 removal target — outside anchored defect lines."""
    return True


def fr_cs4_probe_composed(expression: str = "1 + 1") -> str:
    """Push 1: root gates defect invocation. Push 2: drop root + defect call."""
    if _fr_cs4_structural_root():
        _fr_cs4_review_visible_defect(expression)
    return FR_CS4_PROBE_MARKER
