# backend/tests/unit/test_workspace_credit_model.py
"""WorkspaceORM credit columns — metadata and defaults."""
from __future__ import annotations

from sqlalchemy import inspect

from app.models.workspaces import WorkspaceORM


def test_completed_review_runs_column_present():
    cols = {c.key: c for c in inspect(WorkspaceORM).columns}
    assert "completed_review_runs" in cols


def test_completed_review_runs_not_nullable():
    col = inspect(WorkspaceORM).columns["completed_review_runs"]
    assert col.nullable is False


def test_completed_review_runs_server_default():
    col = inspect(WorkspaceORM).columns["completed_review_runs"]
    assert col.server_default.arg == "0"


def test_completed_review_runs_orm_default():
    col = inspect(WorkspaceORM).columns["completed_review_runs"]
    assert col.default is not None
    assert col.default.arg == 0


def test_review_run_limit_column_present():
    cols = {c.key: c for c in inspect(WorkspaceORM).columns}
    assert "review_run_limit" in cols


def test_review_run_limit_nullable():
    col = inspect(WorkspaceORM).columns["review_run_limit"]
    assert col.nullable is True


def test_review_run_limit_no_server_default():
    col = inspect(WorkspaceORM).columns["review_run_limit"]
    assert col.server_default is None