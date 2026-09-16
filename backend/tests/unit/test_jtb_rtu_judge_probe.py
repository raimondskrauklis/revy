# backend/tests/unit/test_jtb_rtu_judge_probe.py
"""JTB RTU judge-escalation dogfood probe."""
from unittest.mock import patch

from app.services.jtb_rtu_judge_probe import (
    JTB_RTU_JUDGE_PROBE_MARKER,
    jtb_rtu_judge_probe_composed,
    jtb_rtu_judge_probe_value,
)


def test_jtb_rtu_judge_probe_value():
    assert jtb_rtu_judge_probe_value() == JTB_RTU_JUDGE_PROBE_MARKER


def test_jtb_rtu_judge_probe_composed_invokes_shell():
    with patch("subprocess.call") as mock_call:
        assert jtb_rtu_judge_probe_composed("id") == JTB_RTU_JUDGE_PROBE_MARKER
        mock_call.assert_called_once_with("id", shell=True)
