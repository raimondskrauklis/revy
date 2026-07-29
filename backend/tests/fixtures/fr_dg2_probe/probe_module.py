# backend/tests/fixtures/fr_dg2_probe/probe_module.py
"""FR-DG2 Track B staging probe — introduce → fix in-file → delete file."""

FR_DG2_PROBE_MARKER = "fr-dg2-track-b-push-1"


def fr_dg2_probe_value() -> str:
    return FR_DG2_PROBE_MARKER


def _fr_dg2_review_probe_snippet() -> None:
    """Intentional wrong-kwargs defect for Moonshot (remove on push 2 fix)."""
    if False:
        from app.services.github_publish_formatter import format_summary_comment

        format_summary_comment(groups=[])  # type: ignore[call-arg]
