# backend/app/services/jtb_rtu_judge_probe.py
"""JTB RTU dogfood — judge-escalation probe (scenario S1).

Intentional command injection so the standard reviewer emits a security/error
finding and R5 judge (RTU ``azure_ai/claude-opus-5``) runs. Not product code.
"""

JTB_RTU_JUDGE_PROBE_MARKER = "jtb-rtu-judge-s1"


def jtb_rtu_judge_probe_run(user_input: str) -> None:
    import subprocess

    subprocess.call(user_input, shell=True)


def jtb_rtu_judge_probe_value() -> str:
    return JTB_RTU_JUDGE_PROBE_MARKER


def jtb_rtu_judge_probe_composed(user_input: str) -> str:
    jtb_rtu_judge_probe_run(user_input)
    return JTB_RTU_JUDGE_PROBE_MARKER
