# backend/tests/fixtures/psa_staging/probe_module.py
"""PSA staging dogfood probe — intentional maintainability target for push 2–3 validation.

Push 2: introduce unused marker (expect generation finding).
Push 3: wire marker into return value (expect G9 / thread collapse / block-2 shrink).
Push 4 (optional): re-introduce unused marker.
"""

PSA_STAGING_PROBE_MARKER = "psa-dogfood-push-2"


def psa_staging_probe_value() -> str:
    """Stable value for unit tests; marker intentionally unused until push 3."""
    return "psa-staging-ok"
