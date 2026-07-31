# backend/tests/unit/test_fr_cs4_probe.py
"""FR-CS4 D1 — staging probe import hook."""
from unittest.mock import patch

from app.services.fr_cs4_staging_probe import (
    FR_CS4_PROBE_MARKER,
    fr_cs4_probe_composed,
    fr_cs4_probe_value,
)


def test_fr_cs4_probe_importable():
    assert fr_cs4_probe_value() == FR_CS4_PROBE_MARKER


def test_fr_cs4_probe_composed_returns_marker_without_defect():
    with patch(
        "app.services.fr_cs4_staging_probe._fr_cs4_review_visible_defect",
    ) as mock_defect:
        assert fr_cs4_probe_composed() == FR_CS4_PROBE_MARKER
        mock_defect.assert_not_called()
