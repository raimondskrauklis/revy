# backend/app/services/fr_cs4_staging_probe.py
"""FR-CS4 staging probe — structural fix without line touch (D1.1).

Attempt 5 (D1-O11): ``app/services`` path (not ``dogfood/``). Push 2 removes
``_fr_cs4_structural_root`` and stops invoking the defect — **do not edit**
``_fr_cs4_review_visible_defect`` body (Pass 1a line-region guard).
"""

FR_CS4_PROBE_MARKER = "fr-cs4-push-1"


def _fr_cs4_review_visible_defect() -> float:
    """Anchored defect — leave this function body unchanged on push 2."""
    return 1.0 / 0.0  # intentional dogfood divide-by-zero


def fr_cs4_probe_value() -> str:
    """Stable import hook for unit tests."""
    return FR_CS4_PROBE_MARKER


def _fr_cs4_structural_root() -> bool:
    """Push-2 removal target — outside anchored defect lines."""
    return True


def fr_cs4_probe_composed() -> str:
    """Push 1: root gates defect invocation. Push 2: drop root + defect call."""
    if _fr_cs4_structural_root():
        _fr_cs4_review_visible_defect()
    return FR_CS4_PROBE_MARKER
