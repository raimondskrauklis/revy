# backend/app/services/jtb_rtu_judge_probe.py
"""JTB RTU dogfood — S3: probe marker only (command injection removed)."""

JTB_RTU_JUDGE_PROBE_MARKER = "jtb-rtu-judge-s3"


def jtb_rtu_judge_probe_run(user_input: str) -> None:
    _ = user_input


def jtb_rtu_judge_probe_value() -> str:
    return JTB_RTU_JUDGE_PROBE_MARKER


def jtb_rtu_judge_probe_composed(user_input: str) -> str:
    jtb_rtu_judge_probe_run(user_input)
    return JTB_RTU_JUDGE_PROBE_MARKER
