# backend/tests/unit/test_fr_dg2_track_c_probe.py
"""Track C dogfood probe import hook."""
from tests.fixtures.fr_dg2_track_c.probe_module import (
    TRACK_C_STAGING_MARKER,
    fr_dg2_track_c_probe_value,
)


def test_fr_dg2_track_c_probe_importable():
    assert fr_dg2_track_c_probe_value() == TRACK_C_STAGING_MARKER
