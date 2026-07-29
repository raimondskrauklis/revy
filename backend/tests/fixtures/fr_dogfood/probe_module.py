# backend/tests/fixtures/fr_dogfood/probe_module.py
"""FR-DG staging probe — wire marker on push 2; remove on push 3 after P2 deploy."""

FR_DOGFOOD_PROBE_MARKER = "fr-dogfood-push-2"


def fr_dogfood_probe_value() -> str:
    """Stable return for unit tests; marker unused until dogfood push 2."""
    return "fr-dogfood-ok"
