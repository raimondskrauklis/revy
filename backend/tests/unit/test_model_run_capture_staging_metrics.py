# backend/tests/unit/test_model_run_capture_staging_metrics.py
"""Model run capture staging metrics — gate evaluation."""
from scripts.model_run_capture_staging_metrics import (
    _evaluate_mrc_p0_gate,
    _evaluate_mrc_p1_gate,
)


def _metrics(
    *,
    alembic: str = "2026_08_10_1300_0032_github_pipeline_runs_models_snapshot",
    column_exists: bool = True,
    with_embed: int = 2,
    embed_with_model: int = 2,
    embed_step_match: int = 2,
    false_reuse: int = 0,
    embed_attempts: int = 4,
    with_request_model: int = 4,
    parity_pass: int = 2,
    parity_fail: int = 0,
    judge_steps: int = 2,
    judge_with_model: int = 2,
    publish_steps: int = 2,
    publish_with_model: int = 2,
) -> dict:
    return {
        "alembic_version": alembic,
        "models_snapshot_column_exists": column_exists,
        "index_identity": {
            "with_embed": with_embed,
            "embed_with_model_in_manifest": embed_with_model,
            "embed_step_model_match": embed_step_match,
            "reuse_false_model": false_reuse,
        },
        "index_embed_attempts": {
            "index_embed_attempts": embed_attempts,
            "with_request_model": with_request_model,
        },
        "embed_model_parity": {
            "parity_pass": parity_pass,
            "parity_fail": parity_fail,
        },
        "step_models": [
            {
                "step_type": "judge",
                "total_steps": judge_steps,
                "with_model_fields": judge_with_model,
            },
            {
                "step_type": "publish",
                "total_steps": publish_steps,
                "with_model_fields": publish_with_model,
            },
        ],
        "models_snapshot": {"pipeline_runs": 2, "with_snapshot": 0},
    }


def test_mrc_p0_gate_passes_happy_path():
    gate = _evaluate_mrc_p0_gate(_metrics(), require_runs=False)
    assert gate["passed"] is True


def test_mrc_p0_gate_fails_wrong_alembic():
    gate = _evaluate_mrc_p0_gate(_metrics(alembic="0031"), require_runs=False)
    assert gate["passed"] is False


def test_mrc_p1_gate_passes_happy_path():
    gate = _evaluate_mrc_p1_gate(_metrics(), require_runs=False)
    assert gate["passed"] is True


def test_mrc_p1_gate_fails_parity_mismatch():
    gate = _evaluate_mrc_p1_gate(_metrics(parity_fail=1), require_runs=False)
    assert gate["passed"] is False
