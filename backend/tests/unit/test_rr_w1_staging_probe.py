# backend/tests/unit/test_rr_w1_staging_probe.py
"""RR-W1 staging probe import hook."""
from unittest.mock import patch

from app.services.rr_w1_staging_probe import (
    RR_W1_PROBE_MARKER,
    rr_w1_probe_composed,
    rr_w1_probe_invoke,
    rr_w1_probe_value,
)


def test_rr_w1_probe_importable():
    assert rr_w1_probe_value() == RR_W1_PROBE_MARKER


def test_rr_w1_probe_invoke_routes_to_composed():
    with patch(
        "app.services.rr_w1_staging_probe._rr_w1_review_visible_defect",
    ) as mock_defect:
        assert rr_w1_probe_invoke("echo") == RR_W1_PROBE_MARKER
        mock_defect.assert_not_called()


def test_rr_w1_probe_composed_returns_marker_without_defect():
    with patch(
        "app.services.rr_w1_staging_probe._rr_w1_review_visible_defect",
    ) as mock_defect:
        assert rr_w1_probe_composed() == RR_W1_PROBE_MARKER
        mock_defect.assert_not_called()
