# backend/tests/unit/test_reconcile_tasks.py
"""Reconciliation Celery tasks — R5."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.workers import reconcile_tasks


def test_reconcile_review_run_task_runs():
    review_run_id = uuid.uuid4()

    session = AsyncMock()
    session.commit = AsyncMock()

    db_context = MagicMock()
    db_context.__aenter__ = AsyncMock(return_value=session)
    db_context.__aexit__ = AsyncMock(return_value=None)

    with patch("app.workers.reconcile_tasks.get_db_context", return_value=db_context):
        with patch(
            "app.workers.reconcile_tasks.reconcile_review_run",
            AsyncMock(return_value=[uuid.uuid4()]),
        ) as reconcile_mock:
            with patch(
                "app.workers.reconcile_tasks.run_judge_for_review_run",
                AsyncMock(return_value=0),
            ) as judge_mock:
                reconcile_tasks.reconcile_review_run_task.run(str(review_run_id))

    reconcile_mock.assert_awaited_once()
    judge_mock.assert_awaited_once()
    session.commit.assert_awaited_once()
