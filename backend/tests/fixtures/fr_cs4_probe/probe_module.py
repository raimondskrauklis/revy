# backend/tests/fixtures/fr_cs4_probe/probe_module.py
"""FR-CS4 staging probe — structural fix without line touch (D1.1 push 1).

Push 1: Moonshot flags bare ``except`` in ``_fr_cs4_review_visible_defect`` (D1-O1;
post-M0 formatter kwargs pattern silent on #72 rev 1).
Push 2: remove ``_fr_cs4_structural_root`` and stop invoking the defect from
``fr_cs4_probe_composed`` — **do not edit** the defect function body (Pass 1a
line-region guard). Pass 3 verification judge closes ``still_open`` groups.
"""

FR_CS4_PROBE_MARKER = "fr-cs4-push-1"


def _fr_cs4_review_visible_defect() -> int:
    """Anchored defect — leave this function body unchanged on push 2."""
    try:
        return int("not-a-number")
    except:  # noqa: E722 — intentional bare except for dogfood probe
        return -1


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
