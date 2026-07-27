# backend/tests/unit/test_index_tasks.py
"""Indexing Celery tasks — R3."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.constants.enums import GitHubIndexJobStatus, GitHubIndexJobTriggerSource
from app.models.github_index_job import GitHubIndexJobORM
from app.services.review_pipeline import ReviewAfterIndexOutcome
from app.workers import index_tasks


def test_index_pull_request_revision_runs_job():
    job = GitHubIndexJobORM(
        revision_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        status=GitHubIndexJobStatus.completed,
        chunk_count=3,
    )
    job.id = uuid.uuid4()
    review_run_id = uuid.uuid4()

    session = AsyncMock()

    db_context = MagicMock()
    db_context.__aenter__ = AsyncMock(return_value=session)
    db_context.__aexit__ = AsyncMock(return_value=None)

    with patch("app.workers.index_tasks.get_db_context", return_value=db_context):
        with patch(
            "app.workers.index_tasks.run_index_job",
            AsyncMock(return_value=job),
        ) as run_mock:
            with patch(
                "app.workers.index_tasks.prepare_review_after_index",
                AsyncMock(return_value=ReviewAfterIndexOutcome(review_run_id=review_run_id)),
            ):
                with patch("app.workers.index_tasks.enqueue_review_run") as enqueue_mock:
                    index_tasks.index_pull_request_revision.run(str(job.id))

    run_mock.assert_awaited_once()
    enqueue_mock.assert_called_once()


def test_index_pull_request_revision_finalizes_check_when_review_enqueue_fails():
    revision_id = uuid.uuid4()
    job = GitHubIndexJobORM(
        revision_id=revision_id,
        workspace_id=uuid.uuid4(),
        status=GitHubIndexJobStatus.pending,
        trigger_source=GitHubIndexJobTriggerSource.autostart,
        chunk_count=3,
    )
    job.id = uuid.uuid4()
    pipeline_run_id = uuid.uuid4()

    revision = MagicMock()
    revision.head_sha = "abc"

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[job, revision])
    session.flush = AsyncMock()

    db_context = MagicMock()
    db_context.__aenter__ = AsyncMock(return_value=session)
    db_context.__aexit__ = AsyncMock(return_value=None)

    pipeline_run = MagicMock()
    pipeline_run.id = pipeline_run_id
    completed_job = GitHubIndexJobORM(
        revision_id=revision_id,
        workspace_id=job.workspace_id,
        status=GitHubIndexJobStatus.completed,
        trigger_source=GitHubIndexJobTriggerSource.autostart,
        chunk_count=3,
    )
    completed_job.id = job.id

    with patch("app.workers.index_tasks.get_db_context", return_value=db_context):
        with patch(
            "app.workers.index_tasks.run_index_job",
            AsyncMock(return_value=completed_job),
        ):
            with patch(
                "app.workers.index_tasks.ensure_pipeline_run_for_index_job",
                AsyncMock(return_value=pipeline_run),
            ):
                with patch(
                    "app.workers.index_tasks.start_pipeline_github_check",
                    AsyncMock(return_value=99),
                ):
                    with patch(
                        "app.workers.index_tasks.stash_pipeline_github_check_run_id",
                        AsyncMock(),
                    ):
                        with patch(
                            "app.workers.index_tasks.record_index_pipeline_step",
                            AsyncMock(),
                        ):
                            with patch(
                                "app.workers.index_tasks.prepare_review_after_index",
                                AsyncMock(
                                    return_value=ReviewAfterIndexOutcome(
                                        fail_pipeline_check=True,
                                        pipeline_check_summary="llm_disabled",
                                    )
                                ),
                            ):
                                with patch(
                                    "app.workers.index_tasks.finalize_pipeline_github_check_failure",
                                    AsyncMock(),
                                ) as finalize_mock:
                                    with patch("app.workers.index_tasks.enqueue_review_run"):
                                        index_tasks.index_pull_request_revision.run(str(job.id))

    finalize_mock.assert_awaited_once()
    assert db_context.__aenter__.await_count == 2
