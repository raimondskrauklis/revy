# backend/tests/fixtures/fr_dogfood/probe_module.py
"""FR-DG staging probe — wired push 2a; introduce push 2b; fix push 2c; remove push 3."""

FR_DOGFOOD_PROBE_MARKER = "fr-dogfood-push-2"


def fr_dogfood_probe_value() -> str:
    """Return wired marker (push 2a). Review findings from push 2b fixed in push 2c."""
    return FR_DOGFOOD_PROBE_MARKER
