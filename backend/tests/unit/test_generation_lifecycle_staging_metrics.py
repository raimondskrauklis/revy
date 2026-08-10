# backend/tests/unit/test_generation_lifecycle_staging_metrics.py
"""Generation lifecycle staging metrics — RG-15 gate evaluation."""
from scripts.generation_lifecycle_staging_metrics import _evaluate_rg15_gate


def test_rg15_gate_passes_no_stuck_processing():
    gate = _evaluate_rg15_gate(
        {
            "review_runs": {
                "total_runs": 5,
                "processing_runs": 0,
                "superseded_review_runs": 2,
            },
            "index_jobs": {
                "total_jobs": 6,
                "processing_jobs": 0,
                "superseded_index_jobs": 1,
            },
            "revisions": {"revision_count": 6},
        },
        require_activity=False,
    )
    assert gate["passed"] is True
    supersede = next(c for c in gate["checks"] if c["name"] == "supersede_path")
    assert supersede["status"] == "PASS"


def test_rg15_gate_passes_review_run_supersede_status():
    gate = _evaluate_rg15_gate(
        {
            "review_runs": {"total_runs": 3, "processing_runs": 0, "superseded_review_runs": 1},
            "index_jobs": {"total_jobs": 2, "processing_jobs": 0, "superseded_index_jobs": 0},
            "revisions": {"revision_count": 3},
        },
        require_activity=False,
    )
    assert gate["passed"] is True


def test_rg15_gate_fails_stuck_processing():
    gate = _evaluate_rg15_gate(
        {
            "review_runs": {"total_runs": 1, "processing_runs": 1, "superseded_review_runs": 0},
            "index_jobs": {"total_jobs": 0, "processing_jobs": 0, "superseded_index_jobs": 0},
            "revisions": {"revision_count": 1},
        },
        require_activity=False,
    )
    assert gate["passed"] is False
