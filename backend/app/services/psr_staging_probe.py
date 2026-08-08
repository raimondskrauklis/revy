# backend/app/services/psr_staging_probe.py
"""PSR staging probe — post-deploy PR summary rollup dogfood marker.

Safe import-only fixture for multi-revision staging validation (push 1 baseline).
"""

PSR_PROBE_MARKER = "psr-staging-push-1"


def psr_probe_value() -> str:
    return PSR_PROBE_MARKER
