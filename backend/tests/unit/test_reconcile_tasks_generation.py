# backend/tests/unit/test_reconcile_tasks_generation.py
"""Reconcile task generation lifecycle guards — P2."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.constants.enums import GitHubReviewRunStatus, ReviewProfile
from app.models.github_review_run import GitHubReviewRunORM
from app.workers import reconcile_tasks


def test_reconcile_skips_publish_enqueue_when_run_superseded():
    review_run_id = uuid.uuid4()
    run = GitHubReviewRunORM(
        revision_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        status=GitHubReviewRunStatus.superseded,
        profile=ReviewProfile.standard,
    )
    run.id = review_run_id

    session = AsyncMock()
    session.get = AsyncMock(return_value=run)
    session.commit = AsyncMock()

    db_context = MagicMock()
    db_context.__aenter__ = AsyncMock(return_value=session)
    db_context.__aexit__ = AsyncMock(return_value=None)

    with patch("app.workers.reconcile_tasks.get_db_context", return_value=db_context):
        with patch(
            "app.workers.reconcile_tasks.reconcile_review_run",
            AsyncMock(return_value=[]),
        ):
            with patch(
                "app.workers.reconcile_tasks.record_review_run_judge_status",
                AsyncMock(return_value=0),
            ):
                with patch(
                    "app.workers.reconcile_tasks.get_pipeline_run_for_review_run",
                    AsyncMock(return_value=None),
                ):
                    with patch(
                        "app.workers.reconcile_tasks.enqueue_publish_for_review_run",
                    ) as enqueue_mock:
                        reconcile_tasks.reconcile_review_run_task.run(str(review_run_id))

    session.commit.assert_awaited_once()
    enqueue_mock.assert_not_called()
