# backend/tests/unit/test_psr_staging_probe.py
"""PSR staging probe import hook."""
from app.services.psr_staging_probe import PSR_PROBE_MARKER, psr_probe_value


def test_psr_probe_importable():
    assert psr_probe_value() == PSR_PROBE_MARKER
