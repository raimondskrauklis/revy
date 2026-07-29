# backend/tests/unit/test_fr_dg2_probe.py
"""FR-DG2 Track B staging probe unit test."""
from tests.fixtures.fr_dg2_probe.probe_module import (
    FR_DG2_PROBE_MARKER,
    fr_dg2_probe_value,
)


def test_fr_dg2_probe_module_returns_stable_value():
    assert fr_dg2_probe_value() == FR_DG2_PROBE_MARKER
    assert FR_DG2_PROBE_MARKER == "fr-dg2-track-b-push-2"
