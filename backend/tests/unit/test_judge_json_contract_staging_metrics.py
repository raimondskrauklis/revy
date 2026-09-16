# backend/tests/unit/test_judge_json_contract_staging_metrics.py
"""RCX P7 — staging metrics RCX gate evaluation."""
from scripts.judge_json_contract_staging_metrics import (
    _evaluate_rcx_gate,
    _summarize_publish_summary,
)


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


def test_evaluate_rcx_gate_fails_reverse_cross_check_mismatch():
    gate = _evaluate_rcx_gate(_metrics(engineering_injected_ctx=0, retrieve_injected=1))
    cross = next(c for c in gate["checks"] if c["name"] == "retrieve_manifest_inject_cross_check")
    assert cross["status"] == "FAIL"
    assert "context_stats count 0" in cross["detail"]
    assert gate["passed"] is False


def test_evaluate_rcx_gate_inconclusive_zero_runs():
    gate = _evaluate_rcx_gate(_metrics(runs=0))
    assert gate["passed"] is True
    assert all(check["status"] == "INCONCLUSIVE" for check in gate["checks"])


def test_summarize_publish_summary_maps_row():
    summary = _summarize_publish_summary(
        {
            "completed_jobs": 3,
            "generation_active_count_p50": 1,
            "pr_active_count_p50": 2,
            "resolution_addressed_sum": 4,
            "jobs_with_resolution_addressed": 2,
            "transitions_addressed_sum": 5,
            "denominator_active_prior_sum": 6,
            "jobs_with_denominator_active_prior": 1,
        }
    )
    assert summary["completed_jobs"] == 3
    assert summary["generation_active_count_p50"] == 1
    assert summary["pr_active_count_p50"] == 2
    assert summary["resolution_addressed_sum"] == 4
    assert summary["transitions_addressed_sum"] == 5
    assert summary["denominator_active_prior_sum"] == 6
    assert summary["jobs_with_denominator_active_prior"] == 1


def test_summarize_publish_summary_empty_row():
    assert _summarize_publish_summary(None) == {}


def test_content_shape_text_later_vs_thinking_only():
    from scripts.judge_json_contract_staging_metrics import _content_shape

    later = (
        '[{"type": "thinking", "thinking": "", "signature": "x"},'
        '{"type": "text", "text": "{}"}]'
    )
    only = '[{"type": "thinking", "thinking": "", "signature": "x"}]'
    assert _content_shape(later) == "text_later"
    assert _content_shape(only) == "thinking_only"


def test_classify_failure_row_keeps_live_json_invalid_token():
    from scripts.judge_json_contract_staging_metrics import _classify_failure_row

    assert _classify_failure_row("judge_json_invalid", "not-json") == "invalid_json"
    assert _classify_failure_row("judge_empty_text", None) == "thinking_only"
    assert _classify_failure_row("Anthropic response invalid", None) == "transport"


def test_failure_split_sql_filters_completed_runs():
    from scripts.judge_json_contract_staging_metrics import (
        _FAILURE_SPLIT_SQL,
        _MANIFEST_CANDIDATES_SQL,
    )

    assert "rr.status = 'completed'" in _FAILURE_SPLIT_SQL
    assert "rr.status = 'completed'" in _MANIFEST_CANDIDATES_SQL


def test_summarize_thinking_split_does_not_blend_45_and_8():
    from scripts.judge_json_contract_staging_metrics import _summarize_thinking_split

    rows = (
        [
            {
                "parse_error": "Anthropic response invalid",
                "raw_response_text": '[{"type": "thinking"},{"type": "text"}]',
                "retry_count": 0,
            }
        ]
        * 45
        + [
            {
                "parse_error": "Anthropic response invalid",
                "raw_response_text": '[{"type": "thinking"}]',
                "retry_count": 0,
            }
        ]
        * 8
    )
    summary = _summarize_thinking_split(rows)
    assert summary["text_later"] == 45
    assert summary["thinking_only"] == 8
    assert summary["failure_rows"] == 53
