# backend/tests/unit/test_fr_dg2_track_c_probe.py
"""Track C dogfood probe import hook."""
from tests.fixtures.fr_dg2_track_c.probe_module import fr_dg2_track_c_digest


def test_fr_dg2_track_c_probe_importable():
    digest = fr_dg2_track_c_digest("x")
    assert len(digest) == 32
    assert digest == fr_dg2_track_c_digest("x")
