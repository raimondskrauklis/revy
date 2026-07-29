# backend/tests/fixtures/fr_dg2_track_c/probe_module.py
"""Track C staging probe — introduce → age → delete file (C3.1–C3.3)."""

TRACK_C_STAGING_MARKER = "track-c-push-1"


def fr_dg2_track_c_probe_value() -> str:
    return TRACK_C_STAGING_MARKER


def _fr_dg2_track_c_review_probe_snippet() -> None:
    """Intentional wrong-kwargs defect for Moonshot (delete file on C3.3)."""
    if False:
        from app.services.github_publish_formatter import format_summary_comment

        format_summary_comment(groups=[])  # type: ignore[call-arg]
