# backend/tests/unit/test_revy_review_dogfood_staging_validation.py
"""RR-W1 staging validation script — gate evaluation."""
from scripts.revy_review_dogfood_staging_validation import _evaluate_rr_v_gates


def test_rr_v_gate_pending_with_insufficient_runs():
    gate = _evaluate_rr_v_gates(
        {
            "revisions": [{"rows_per_head_sha": 1}],
            "review_runs": [{"status": "completed", "publish_status": "completed", "head_sha": "a", "publish_head_sha": "a"}],
            "resolution_passes": [],
            "publish_jobs": [],
            "finding_groups": [],
        }
    )
    assert gate["ready_for_signoff"] is False
    statuses = {c["name"]: c["status"] for c in gate["checks"]}
    assert statuses["RR-V2_resolution_stamp"] == "PENDING"


def test_rr_v_gate_passes_with_five_runs_and_addressed():
    gate = _evaluate_rr_v_gates(
        {
            "revisions": [{"rows_per_head_sha": 1}, {"rows_per_head_sha": 1}],
            "review_runs": [
                {
                    "status": "completed",
                    "publish_status": "completed",
                    "head_sha": f"sha{i}",
                    "publish_head_sha": f"sha{i}",
                    "judge_escalation_candidate_count": 1 if i == 4 else 0,
                    "judge_outcomes": 1 if i == 4 else 0,
                }
                for i in range(5)
            ],
            "resolution_passes": [
                {"resolution_pass": {"transitions_addressed": 1, "resolution_rate_pct": 50.0}}
            ],
            "publish_jobs": [{"thread_resolve_skipped": {"thread_id_not_found": 0}}],
            "finding_groups": [{"state": "resolved", "resolution_status": "addressed"}],
        }
    )
    assert gate["ready_for_signoff"] is True
