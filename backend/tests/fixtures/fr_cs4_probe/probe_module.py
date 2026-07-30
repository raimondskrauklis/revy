# backend/tests/fixtures/fr_cs4_probe/probe_module.py
"""FR-CS4 staging probe — structural fix without line touch (D1.1 push 1).

Push 1: Moonshot flags wrong-kwargs lines in ``_fr_cs4_review_visible_defect``.
Push 2: remove ``_fr_cs4_structural_root`` and stop invoking the defect from
``fr_cs4_probe_composed`` — **do not edit** the defect function body (Pass 1a
line-region guard). Pass 3 verification judge closes ``still_open`` groups.
"""

FR_CS4_PROBE_MARKER = "fr-cs4-push-1"


def _fr_cs4_review_visible_defect() -> None:
    """Anchored defect — leave this function body unchanged on push 2."""
    from app.services.github_publish_formatter import format_summary_comment

    format_summary_comment(groups=[])  # type: ignore[call-arg]


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
