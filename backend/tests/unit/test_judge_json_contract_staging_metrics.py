# backend/tests/unit/test_judge_json_contract_staging_metrics.py
"""RCX P7 — staging metrics RCX gate evaluation."""
from scripts.judge_json_contract_staging_metrics import _evaluate_rcx_gate


def _metrics(
    *,
    runs: int = 1,
    runs_with_context_stats: int = 1,
    engineering_injected_ctx: int = 1,
    engineering_bytes_p50: int = 4096,
    runs_with_omitted_md: int = 0,
    diff_truncated_pct: float = 0.0,
    retrieve_injected: int = 1,
) -> dict:
    return {
        "review_context": {
            "retrieve_manifest": {
                "runs": runs,
                "runs_with_omitted_md": runs_with_omitted_md,
                "diff_truncated_pct": diff_truncated_pct,
                "engineering_context_injected_runs": retrieve_injected,
            },
            "context_stats": {
                "runs_with_context_stats": runs_with_context_stats,
                "engineering_context_injected_runs": engineering_injected_ctx,
                "engineering_context_bytes_p50": engineering_bytes_p50,
            },
        }
    }


def test_evaluate_rcx_gate_passes_happy_path():
    gate = _evaluate_rcx_gate(_metrics())
    assert gate["passed"] is True
    assert all(check["status"] != "FAIL" for check in gate["checks"])


def test_evaluate_rcx_gate_fails_on_omitted_md():
    gate = _evaluate_rcx_gate(_metrics(runs_with_omitted_md=2))
    assert gate["passed"] is False
    omitted = next(c for c in gate["checks"] if c["name"] == "runs_with_omitted_md")
    assert omitted["status"] == "FAIL"


def test_evaluate_rcx_gate_inconclusive_diff_truncated_with_one_run():
    gate = _evaluate_rcx_gate(_metrics(runs=1, diff_truncated_pct=25.0))
    diff_check = next(c for c in gate["checks"] if c["name"] == "diff_truncated_pct")
    assert diff_check["status"] == "INCONCLUSIVE"
    assert gate["passed"] is True


def test_evaluate_rcx_gate_fails_cross_check_mismatch():
    gate = _evaluate_rcx_gate(_metrics(retrieve_injected=0))
    cross = next(c for c in gate["checks"] if c["name"] == "retrieve_manifest_inject_cross_check")
    assert cross["status"] == "FAIL"
    assert gate["passed"] is False


def test_evaluate_rcx_gate_inconclusive_zero_runs():
    gate = _evaluate_rcx_gate(_metrics(runs=0))
    assert gate["passed"] is True
    assert all(check["status"] == "INCONCLUSIVE" for check in gate["checks"])
