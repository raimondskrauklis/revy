# backend/tests/unit/test_post_main_staging_probe.py
"""Post-main staging dogfood probe import hook."""
from app.services.post_main_staging_probe import (
    POST_MAIN_PROBE_MARKER,
    post_main_probe_composed,
    post_main_probe_value,
)


def test_post_main_probe_importable():
    assert post_main_probe_value() == POST_MAIN_PROBE_MARKER
    assert post_main_probe_composed() == POST_MAIN_PROBE_MARKER
