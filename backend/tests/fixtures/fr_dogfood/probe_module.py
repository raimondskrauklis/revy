# backend/tests/fixtures/fr_dogfood/probe_module.py
"""FR-DG staging probe — wired push 2a; fix push 2b; remove push 3."""

FR_DOGFOOD_PROBE_MARKER = "fr-dogfood-push-2"


def fr_dogfood_probe_value() -> str:
    """Dogfood push 2a: expose wired marker (review target for FR-DG1 fix push)."""
    return FR_DOGFOOD_PROBE_MARKER
