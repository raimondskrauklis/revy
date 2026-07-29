# backend/tests/fixtures/fr_dg2_probe/probe_module.py
"""FR-DG2 Track B staging probe — introduce → fix in-file → delete file."""

FR_DG2_PROBE_MARKER = "fr-dg2-track-b-push-2"


def fr_dg2_probe_value() -> str:
    """Return wired marker; push 2 removes wrong-kwargs defect from push 1."""
    return FR_DG2_PROBE_MARKER
