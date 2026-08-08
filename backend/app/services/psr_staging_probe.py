# backend/app/services/psr_staging_probe.py
"""PSR staging probe — post-deploy PR summary rollup dogfood marker.

Safe import-only fixture for multi-revision staging validation (push 1 baseline).
"""

PSR_PROBE_MARKER = "psr-staging-push-2"


def psr_probe_value() -> str:
    return PSR_PROBE_MARKER


def psr_probe_composed() -> str:
    """Return marker for multi-revision rollup validation (push 2)."""
    return PSR_PROBE_MARKER
