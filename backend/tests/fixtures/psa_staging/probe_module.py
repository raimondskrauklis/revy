# backend/tests/fixtures/psa_staging/probe_module.py
"""PSA staging dogfood probe — ephemeral; remove after finding-resolution dogfood.

Push 2: unused marker introduced.
Push 3: marker wired into return value.
Push 4: marker unwired again (unused) — expect generation finding on marker.
"""

PSA_STAGING_PROBE_MARKER = "psa-dogfood-push-4"


def psa_staging_probe_value() -> str:
    """Stable return for unit tests; marker intentionally unused on push 4."""
    return "psa-staging-ok"
