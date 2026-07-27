# backend/tests/unit/test_index_tasks_generation.py
"""Index task generation lifecycle guards — P2."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.constants.enums import GitHubIndexJobStatus, GitHubIndexJobTriggerSource
from app.models.github_index_job import GitHubIndexJobORM
from app.services.review_pipeline import ReviewAfterIndexOutcome
from app.workers import index_tasks


def test_index_pull_request_revision_skips_pipeline_when_not_authoritative():
    revision_id = uuid.uuid4()
    job = GitHubIndexJobORM(
        revision_id=revision_id,
        workspace_id=uuid.uuid4(),
        status=GitHubIndexJobStatus.pending,
        trigger_source=GitHubIndexJobTriggerSource.autostart,
    )
    job.id = uuid.uuid4()

    revision = MagicMock()
    revision.head_sha = "stale-sha"

    session = AsyncMock()
    session.get = AsyncMock(side_effect=[job, revision])

    db_context = MagicMock()
    db_context.__aenter__ = AsyncMock(return_value=session)
    db_context.__aexit__ = AsyncMock(return_value=None)

    completed_job = GitHubIndexJobORM(
        revision_id=revision_id,
        workspace_id=job.workspace_id,
        status=GitHubIndexJobStatus.completed,
        trigger_source=GitHubIndexJobTriggerSource.autostart,
        chunk_count=1,
    )
    completed_job.id = job.id

    with patch("app.workers.index_tasks.get_db_context", return_value=db_context):
        with patch(
            "app.workers.index_tasks.is_authoritative_for_pull_request_head",
            AsyncMock(return_value=False),
        ):
            with patch(
                "app.workers.index_tasks.ensure_pipeline_run_for_index_job",
                AsyncMock(),
            ) as ensure_mock:
                with patch(
                    "app.workers.index_tasks.start_pipeline_github_check",
                    AsyncMock(),
                ) as start_mock:
                    with patch(
                        "app.workers.index_tasks.run_index_job",
                        AsyncMock(return_value=completed_job),
                    ):
                        with patch(
                            "app.workers.index_tasks.prepare_review_after_index",
                            AsyncMock(return_value=ReviewAfterIndexOutcome()),
                        ):
                            index_tasks.index_pull_request_revision.run(str(job.id))

    ensure_mock.assert_not_awaited()
    start_mock.assert_not_awaited()
