# backend/tests/fixtures/fr_dogfood/probe_module.py
"""FR-DG staging probe — wired push 2a; defect push 2b; fix push 2c; remove push 3."""

FR_DOGFOOD_PROBE_MARKER = "fr-dogfood-push-2"


def fr_dogfood_probe_value() -> str:
    """Dogfood push 2a: expose wired marker (review target for FR-DG1 fix push)."""
    return FR_DOGFOOD_PROBE_MARKER


def _fr_dogfood_review_probe_snippet() -> None:
    """Dogfood push 2b — wrong format_summary_comment kwargs (PSA #63 class); never executed."""
    if False:
        from app.services.github_publish_formatter import format_summary_comment

        format_summary_comment(groups=[])  # type: ignore[call-arg]
