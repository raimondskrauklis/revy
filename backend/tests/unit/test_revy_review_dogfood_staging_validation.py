# backend/tests/unit/test_revy_review_dogfood_staging_validation.py
"""RR-W1 staging validation script — gate evaluation."""
from scripts.revy_review_dogfood_staging_validation import (
    _evaluate_rr_v_gates,
    _staging_database_url,
)


def test_staging_database_url_prefers_staging_env(monkeypatch):
    monkeypatch.setenv("STAGING_DATABASE_URL", "postgresql://u:p@host:5432/revy-staging")
    monkeypatch.setenv("PRODUCTION_DATABASE_URL", "postgresql://u:p@host:5432/revy-prod")
    assert _staging_database_url().endswith("/revy-staging")


def test_staging_database_url_preserves_non_ssl_query_params(monkeypatch):
    monkeypatch.setenv(
        "PRODUCTION_DATABASE_URL",
        "postgresql+asyncpg://u:p@host:5432/revy-staging?sslmode=require&application_name=rr-v",
    )
    url = _staging_database_url()
    assert "application_name=rr-v" in url
    assert "sslmode" not in url
    gate = _evaluate_rr_v_gates(
        {
            "revisions": [{"rows_per_head_sha": 1}],
            "review_runs": [
                {
                    "status": "completed",
                    "publish_status": "completed",
                    "head_sha": "a",
                    "publish_head_sha": "a",
                }
            ],
            "resolution_passes": [],
            "publish_jobs": [],
            "finding_groups": [],
        }
    )
    assert gate["ready_for_signoff"] is False
    statuses = {c["name"]: c["status"] for c in gate["checks"]}
    assert statuses["RR-V2_resolution_stamp"] == "PENDING"


def test_rr_v3_pending_without_completed_publish():
    gate = _evaluate_rr_v_gates(
        {
            "revisions": [],
            "review_runs": [{"status": "completed", "head_sha": "a"}],
            "resolution_passes": [],
            "publish_jobs": [],
            "finding_groups": [],
        }
    )
    statuses = {c["name"]: c["status"] for c in gate["checks"]}
    assert statuses["RR-V3_publish_head_sha_parity"] == "PENDING"


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
            "publish_jobs": [
                {"thread_resolve_skipped": {"resolve_mutation_failed": 2}},
                {"revision_number": 7, "thread_resolve_skipped": {"already_resolved": 1}},
            ],
            "finding_groups": [{"state": "resolved", "resolution_status": "addressed"}],
        }
    )
    assert gate["ready_for_signoff"] is False
    statuses = {c["name"]: c["status"] for c in gate["checks"]}
    assert statuses["RR-V2_resolution_stamp"] == "PASS"
    assert statuses["RR-V5_head_suppression_matrix"] == "PENDING"


def test_rr_v4_passes_when_latest_publish_clean_despite_historical_skips():
    gate = _evaluate_rr_v_gates(
        {
            "revisions": [{"rows_per_head_sha": 1}] * 7,
            "review_runs": [
                {
                    "status": "completed",
                    "publish_status": "completed",
                    "head_sha": f"sha{i}",
                    "publish_head_sha": f"sha{i}",
                }
                for i in range(7)
            ],
            "resolution_passes": [
                {"resolution_pass": {"transitions_addressed": 1, "resolution_rate_pct": 100.0}}
            ],
            "publish_jobs": [
                {"revision_number": 2, "thread_resolve_skipped": {"resolve_mutation_failed": 2}},
                {"revision_number": 7, "thread_resolve_skipped": {"already_resolved": 1}},
            ],
            "finding_groups": [{"state": "resolved", "resolution_status": "addressed"}],
        }
    )
    statuses = {c["name"]: c["status"] for c in gate["checks"]}
    assert statuses["RR-V4_thread_resolve_taxonomy"] == "PASS"
    assert "historical skips" in next(
        c["detail"] for c in gate["checks"] if c["name"] == "RR-V4_thread_resolve_taxonomy"
    )
