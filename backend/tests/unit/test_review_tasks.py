# backend/tests/unit/test_review_tasks.py
"""Review Celery tasks — R4."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.constants.enums import GitHubReviewRunStatus, ReviewProfile
from app.models.github_review_run import GitHubReviewRunORM
from app.services.github_review import ReviewRunOutcome
from app.workers import review_tasks


def test_review_pull_request_revision_skips_trace_when_superseded():
    run = GitHubReviewRunORM(
        revision_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        status=GitHubReviewRunStatus.superseded,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = uuid.uuid4()
    outcome = ReviewRunOutcome(run=run)

    session = AsyncMock()
    session.commit = AsyncMock()

    db_context = MagicMock()
    db_context.__aenter__ = AsyncMock(return_value=session)
    db_context.__aexit__ = AsyncMock(return_value=None)

    with patch("app.workers.review_tasks.get_db_context", return_value=db_context):
        with patch(
            "app.workers.review_tasks.run_review_run",
            AsyncMock(return_value=outcome),
        ):
            with patch(
                "app.workers.review_tasks._record_review_pipeline_trace",
                AsyncMock(),
            ) as trace_mock:
                with patch("app.workers.review_tasks._enqueue_reconcile") as enqueue_mock:
                    review_tasks.review_pull_request_revision.run(str(run.id))

    trace_mock.assert_not_awaited()
    enqueue_mock.assert_not_called()


def test_review_pull_request_revision_runs_job():
    run = GitHubReviewRunORM(
        revision_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = uuid.uuid4()
    outcome = ReviewRunOutcome(run=run)

    session = AsyncMock()
    session.commit = AsyncMock()

    db_context = MagicMock()
    db_context.__aenter__ = AsyncMock(return_value=session)
    db_context.__aexit__ = AsyncMock(return_value=None)

    with patch("app.workers.review_tasks.get_db_context", return_value=db_context):
        with patch(
            "app.workers.review_tasks.run_review_run",
            AsyncMock(return_value=outcome),
        ) as run_mock:
            with patch(
                "app.workers.review_tasks._record_review_pipeline_trace",
                AsyncMock(),
            ):
                with patch("app.workers.review_tasks._enqueue_reconcile") as enqueue_mock:
                    review_tasks.review_pull_request_revision.run(str(run.id))

    run_mock.assert_awaited_once()
    session.commit.assert_awaited_once()
    enqueue_mock.assert_called_once_with(str(run.id))
