# backend/tests/unit/test_fr_cs4_probe.py
"""FR-CS4 D1 — staging probe fixture (push 1)."""
from unittest.mock import patch

from tests.fixtures.fr_cs4_probe.probe_module import (
    FR_CS4_PROBE_MARKER,
    fr_cs4_probe_composed,
    fr_cs4_probe_value,
)


def test_fr_cs4_probe_importable():
    assert fr_cs4_probe_value() == FR_CS4_PROBE_MARKER


def test_fr_cs4_probe_composed_skips_defect_when_root_false():
    with patch(
        "tests.fixtures.fr_cs4_probe.probe_module._fr_cs4_structural_root",
        return_value=False,
    ):
        assert fr_cs4_probe_composed() == FR_CS4_PROBE_MARKER


def test_fr_cs4_probe_composed_invokes_defect_when_root_true():
    with patch(
        "tests.fixtures.fr_cs4_probe.probe_module._fr_cs4_review_visible_defect",
    ) as mock_defect:
        with patch(
            "tests.fixtures.fr_cs4_probe.probe_module._fr_cs4_structural_root",
            return_value=True,
        ):
            assert fr_cs4_probe_composed() == FR_CS4_PROBE_MARKER
            mock_defect.assert_called_once()
