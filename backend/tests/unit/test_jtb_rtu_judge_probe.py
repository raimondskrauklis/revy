# backend/tests/unit/test_jtb_rtu_judge_probe.py
"""JTB RTU judge-escalation dogfood probe."""
from app.services.jtb_rtu_judge_probe import (
    JTB_RTU_JUDGE_PROBE_MARKER,
    jtb_rtu_judge_probe_composed,
    jtb_rtu_judge_probe_value,
)


def test_jtb_rtu_judge_probe_value():
    assert jtb_rtu_judge_probe_value() == JTB_RTU_JUDGE_PROBE_MARKER


def test_jtb_rtu_judge_probe_composed_returns_marker():
    assert jtb_rtu_judge_probe_composed("id") == JTB_RTU_JUDGE_PROBE_MARKER
