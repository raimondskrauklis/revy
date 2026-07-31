# backend/app/services/jt_transport_staging_probe.py
"""JT-T3 staging probe — judge-eligible defect for transport reliability verification.

Push 1 only: intentional command-injection defect (critical/security) so staging
reconcile runs discovery judge against a real candidate. Do not edit the anchored
defect body between pushes — operator records ``review_run_id`` + worker logs.
"""

JT_TRANSPORT_PROBE_MARKER = "jt-transport-t3"


def _jt_transport_review_visible_defect(user_input: str) -> None:
    """Anchored defect — leave this function body unchanged on probe push 1."""
    import subprocess

    subprocess.call(user_input, shell=True)  # intentional staging probe


def jt_transport_probe_value() -> str:
    """Stable import hook for unit tests."""
    return JT_TRANSPORT_PROBE_MARKER


def jt_transport_probe_entry(user_input: str) -> str:
    """Reachable hook — Moonshot/Revy should flag shell injection (judge candidate)."""
    _jt_transport_review_visible_defect(user_input)
    return JT_TRANSPORT_PROBE_MARKER
