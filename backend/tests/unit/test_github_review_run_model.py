# backend/tests/unit/test_github_review_run_model.py
"""GitHub review run ORM — RCX context_stats column."""
from sqlalchemy import inspect

from app.models.github_review_run import GitHubReviewRunORM


def test_github_review_run_has_context_stats_column():
    columns = {column.name for column in inspect(GitHubReviewRunORM).columns}
    assert "context_stats" in columns
