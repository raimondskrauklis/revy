# backend/tests/unit/test_pipeline_observability_schema.py
"""Pipeline observability P0 — ORM + migration registry."""
from sqlalchemy import inspect

from app.constants.enums import (
    GitHubReviewRunFailureClass,
    LlmCallOperationName,
    LlmCallStepType,
)
from app.models import Base, GitHubLlmCallAttemptORM, GitHubReviewRunORM


def test_pipeline_observability_enums():
    assert GitHubReviewRunFailureClass.timeout.value == "timeout"
    assert LlmCallStepType.review.value == "review"
    assert LlmCallOperationName.chat.value == "chat"


def test_llm_call_attempts_table_registered():
    assert "github_llm_call_attempts" in Base.metadata.tables


def test_llm_call_attempt_pipeline_run_cascade():
    fk = next(
        fk
        for fk in inspect(GitHubLlmCallAttemptORM).columns["pipeline_run_id"].foreign_keys
    )
    assert fk.ondelete == "CASCADE"


def test_review_run_observability_columns():
    columns = {column.name for column in inspect(GitHubReviewRunORM).columns}
    assert {
        "timing_stats",
        "token_rollup",
        "failure_stage",
        "failure_class",
        "trigger_source",
    } <= columns
