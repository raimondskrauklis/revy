# backend/tests/unit/test_reconcile_tasks.py
"""Reconciliation Celery tasks — R5."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.services.github_finding_closure import VerificationJudgeResult
from app.workers import reconcile_tasks


def test_reconcile_review_run_task_runs_worker_order():
    review_run_id = uuid.uuid4()

    session = AsyncMock()
    session.commit = AsyncMock()
    session.get = AsyncMock(return_value=None)

    db_context = MagicMock()
    db_context.__aenter__ = AsyncMock(return_value=session)
    db_context.__aexit__ = AsyncMock(return_value=None)

    with patch("app.workers.reconcile_tasks.get_db_context", return_value=db_context):
        with patch(
            "app.workers.reconcile_tasks.reconcile_review_run",
            AsyncMock(return_value=[uuid.uuid4()]),
        ) as reconcile_mock:
            with patch(
                "app.workers.reconcile_tasks.apply_pass2_closure_for_review_run",
                AsyncMock(return_value=1),
            ) as pass2_mock:
                with patch(
                    "app.workers.reconcile_tasks.record_review_run_judge_status",
                    AsyncMock(return_value=2),
                ) as judge_mock:
                    with patch(
                        "app.workers.reconcile_tasks.verify_still_open_escalation_groups",
                        AsyncMock(return_value=VerificationJudgeResult(judged_count=1, artifacts=[])),
                    ) as verification_mock:
                        with patch(
                            "app.workers.reconcile_tasks.enqueue_publish_for_review_run",
                        ) as publish_mock:
                            reconcile_tasks.reconcile_review_run_task.run(str(review_run_id))

    reconcile_mock.assert_awaited_once()
    pass2_mock.assert_awaited_once()
    judge_mock.assert_awaited_once()
    verification_mock.assert_awaited_once()
    publish_mock.assert_called_once()
    session.commit.assert_awaited_once()
