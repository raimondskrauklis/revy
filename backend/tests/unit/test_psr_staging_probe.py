# backend/tests/unit/test_psr_staging_probe.py
"""PSR staging probe import hook."""
from tests.fixtures.psr_staging.probe_module import PSR_PROBE_MARKER, psr_probe_value


def test_psr_probe_importable():
    value = psr_probe_value()
    assert value == PSR_PROBE_MARKER
    assert value.startswith("psr-staging-")
