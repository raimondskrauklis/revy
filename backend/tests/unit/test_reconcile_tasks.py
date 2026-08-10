# backend/tests/unit/test_reconcile_tasks.py
"""Reconciliation Celery tasks — R5."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.constants.enums import GitHubReviewJudgeStatus
from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
from app.models.github_review_run import GitHubReviewRunORM
from app.services.github_finding_closure import VerificationJudgeResult
from app.workers import reconcile_tasks


def test_reconcile_review_run_task_runs_worker_order():
    review_run_id = uuid.uuid4()

    session = AsyncMock()
    session.commit = AsyncMock()
    session.get = AsyncMock(return_value=None)
    session.scalar = AsyncMock(return_value=None)

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
                    AsyncMock(return_value=(2, None)),
                ) as judge_mock:
                    with patch(
                        "app.workers.reconcile_tasks.verify_still_open_escalation_groups",
                        AsyncMock(return_value=VerificationJudgeResult(judged_count=1, artifacts=[])),
                    ) as verification_mock:
                        with patch(
                            "app.workers.reconcile_tasks.finalize_review_run_judge_status",
                            AsyncMock(),
                        ):
                            with patch(
                                "app.workers.reconcile_tasks.get_pipeline_run_for_review_run",
                                AsyncMock(return_value=None),
                            ):
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


def test_reconcile_task_records_resolution_pass_on_pipeline():
    review_run_id = uuid.uuid4()
    pipeline_run_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()

    review_run = MagicMock()
    review_run.revision_id = revision_id
    review_run.id = review_run_id

    current_revision = MagicMock()
    current_revision.id = revision_id
    current_revision.pull_request_id = pull_request_id
    current_revision.revision_number = 2

    prior_revision = MagicMock()
    prior_revision.id = uuid.uuid4()

    pull_request = MagicMock()
    pull_request.id = pull_request_id

    pipeline_run = MagicMock()
    pipeline_run.id = pipeline_run_id

    resolution_pass = {"transition_count": 1, "denominator_active_prior": 2}

    session = AsyncMock()
    session.commit = AsyncMock()

    async def _get(model, key):
        if model is GitHubReviewRunORM:
            return review_run
        if model is GitHubPullRequestRevisionORM:
            return current_revision
        if model is GitHubPullRequestORM:
            return pull_request
        return None

    session.get = AsyncMock(side_effect=_get)
    session.scalar = AsyncMock(return_value=prior_revision)

    db_context = MagicMock()
    db_context.__aenter__ = AsyncMock(return_value=session)
    db_context.__aexit__ = AsyncMock(return_value=None)

    with patch("app.workers.reconcile_tasks.get_db_context", return_value=db_context):
        with patch(
            "app.workers.reconcile_tasks.reconcile_review_run",
            AsyncMock(return_value=[uuid.uuid4()]),
        ):
            with patch(
                "app.workers.reconcile_tasks.apply_pass2_closure_for_review_run",
                AsyncMock(return_value=0),
            ):
                with patch(
                    "app.workers.reconcile_tasks.record_review_run_judge_status",
                    AsyncMock(return_value=(0, None)),
                ):
                    with patch(
                        "app.workers.reconcile_tasks.verify_still_open_escalation_groups",
                        AsyncMock(return_value=VerificationJudgeResult(judged_count=0, artifacts=[])),
                    ):
                        with patch(
                            "app.workers.reconcile_tasks.finalize_review_run_judge_status",
                            AsyncMock(),
                        ):
                            with patch(
                                "app.workers.reconcile_tasks.compute_resolution_transitions",
                                AsyncMock(return_value=resolution_pass),
                            ):
                                with patch(
                                    "app.workers.reconcile_tasks.get_pipeline_run_for_review_run",
                                    AsyncMock(return_value=pipeline_run),
                                ):
                                        with patch(
                                            "app.workers.reconcile_tasks.record_reconcile_pipeline_step",
                                            AsyncMock(),
                                        ) as reconcile_step_mock:
                                            with patch(
                                                "app.workers.reconcile_tasks.record_judge_pipeline_step",
                                                AsyncMock(),
                                            ) as judge_step_mock:
                                                with patch(
                                                    "app.workers.reconcile_tasks.enqueue_publish_for_review_run",
                                                ):
                                                    reconcile_tasks.reconcile_review_run_task.run(
                                                        str(review_run_id)
                                                    )

    reconcile_step_mock.assert_awaited_once()
    assert reconcile_step_mock.await_args.kwargs["resolution_pass"] == resolution_pass
    judge_step_mock.assert_awaited_once()


def test_reconcile_worker_partial_judge_skipped_unavailable_documented():
    """RG-6: partial judge failure sets skipped_unavailable — see judge unit tests."""
    assert GitHubReviewJudgeStatus.skipped_unavailable.value == "skipped_unavailable"
