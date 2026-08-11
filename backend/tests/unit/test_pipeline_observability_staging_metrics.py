# backend/tests/unit/test_pipeline_observability_staging_metrics.py
"""Pipeline observability staging metrics — gate evaluation."""
from scripts.pipeline_observability_staging_metrics import (
    _evaluate_po_gate,
    _evaluate_po_p0_gate,
)
from scripts.staging_metrics_common import StagingScope, model_breakdown_sql


def _metrics(
    *,
    alembic: str = "2026_08_10_1300_0032_github_pipeline_runs_models_snapshot",
    table_exists: bool = True,
    total_runs: int = 3,
    with_timing_stats: int = 3,
    with_trigger_source: int = 3,
    with_retrieve_ms: int = 3,
    attempt_rows: int = 2,
    review_step_attempts: int = 2,
    review_wait_ms_p95: int = 1200,
) -> dict:
    return {
        "alembic_version": alembic,
        "attempts_table_exists": table_exists,
        "review_runs": {
            "total_runs": total_runs,
            "with_timing_stats": with_timing_stats,
            "with_trigger_source": with_trigger_source,
            "with_retrieve_ms": with_retrieve_ms,
        },
        "attempts": {
            "attempt_rows": attempt_rows,
            "review_step_attempts": review_step_attempts,
            "review_wait_ms_p95": review_wait_ms_p95,
        },
        "failure_taxonomy": [{"failure_class": "(success)", "n": 2}],
    }


def test_po_p0_gate_passes_happy_path():
    gate = _evaluate_po_p0_gate(_metrics(), require_runs=False)
    assert gate["passed"] is True


def test_po_p0_gate_fails_wrong_alembic():
    gate = _evaluate_po_p0_gate(_metrics(alembic="0029"), require_runs=False)
    assert gate["passed"] is False


def test_po_p0_gate_inconclusive_no_runs():
    gate = _evaluate_po_p0_gate(
        _metrics(total_runs=0, with_timing_stats=0, with_trigger_source=0, with_retrieve_ms=0),
        require_runs=False,
    )
    assert gate["passed"] is True
    assert all(c["status"] == "INCONCLUSIVE" for c in gate["checks"][2:])


def test_po_gate_passes_with_attempts():
    gate = _evaluate_po_gate(_metrics())
    assert gate["passed"] is True


def test_model_breakdown_sql_pr_scoped_uses_revision_coalesce():
    sql = model_breakdown_sql(
        StagingScope(repo_full_name="owner/repo", pr_number=97, since=None)
    )
    assert "coalesce(pr.revision_id, rr.revision_id, ij.revision_id)" in sql
    assert "model_breakdown" not in sql


def test_model_breakdown_sql_global_aggregates_attempts():
    sql = model_breakdown_sql(StagingScope())
    assert "FROM github_llm_call_attempts" in sql
    assert "GROUP BY 1, 2, 3" in sql
    assert "coalesce(pr.revision_id" not in sql


def test_metrics_json_includes_model_breakdown_shape():
    metrics = _metrics()
    metrics["model_breakdown"] = [
        {
            "step_type": "review",
            "provider": "moonshot",
            "request_model": "kimi-k2.7-code",
            "n": 2,
        }
    ]
    assert metrics["model_breakdown"][0]["step_type"] == "review"
