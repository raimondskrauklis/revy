# backend/tests/unit/test_fr_dogfood_probe.py
"""FR-DG P0 — staging probe fixture."""
from tests.fixtures.fr_dogfood.probe_module import (
    FR_DOGFOOD_PROBE_MARKER,
    fr_dogfood_probe_value,
)


def test_fr_dogfood_probe_module_returns_stable_value():
    assert fr_dogfood_probe_value() == "fr-dogfood-ok"
    assert FR_DOGFOOD_PROBE_MARKER == "fr-dogfood-push-2"
