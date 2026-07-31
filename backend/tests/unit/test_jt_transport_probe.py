# backend/tests/unit/test_jt_transport_probe.py
"""JT-T3 — staging probe import hook."""
from unittest.mock import patch

from app.services.jt_transport_staging_probe import (
    JT_TRANSPORT_PROBE_MARKER,
    jt_transport_probe_entry,
    jt_transport_probe_value,
)


def test_jt_transport_probe_importable():
    assert jt_transport_probe_value() == JT_TRANSPORT_PROBE_MARKER


def test_jt_transport_probe_entry_invokes_defect():
    with patch(
        "app.services.jt_transport_staging_probe._jt_transport_review_visible_defect",
    ) as mock_defect:
        assert jt_transport_probe_entry("echo probe") == JT_TRANSPORT_PROBE_MARKER
        mock_defect.assert_called_once_with("echo probe")
