# backend/tests/unit/test_publish_tasks.py
"""Publish Celery tasks — R6."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.constants.enums import GitHubPublishJobStatus
from app.models.github_publish_job import GitHubPublishJobORM
from app.workers import publish_tasks


def test_publish_review_run_task_runs():
    job = GitHubPublishJobORM(
        review_run_id=uuid.uuid4(),
        revision_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        head_sha="sha",
        status=GitHubPublishJobStatus.completed,
    )
    job.id = uuid.uuid4()

    session = AsyncMock()
    session.commit = AsyncMock()

    db_context = MagicMock()
    db_context.__aenter__ = AsyncMock(return_value=session)
    db_context.__aexit__ = AsyncMock(return_value=None)

    with patch("app.workers.publish_tasks.get_db_context", return_value=db_context):
        with patch(
            "app.workers.publish_tasks.run_publish_job",
            AsyncMock(return_value=job),
        ) as run_mock:
            publish_tasks.publish_review_run.run(str(job.id))

    run_mock.assert_awaited_once()
    session.commit.assert_awaited_once()
    run_mock.assert_awaited_with(
        session,
        publish_job_id=job.id,
        persist_github_surface=True,
    )


def test_publish_for_review_run_enqueues_publish_review_run():
    job_id = uuid.uuid4()

    session = AsyncMock()
    session.commit = AsyncMock()

    db_context = MagicMock()
    db_context.__aenter__ = AsyncMock(return_value=session)
    db_context.__aexit__ = AsyncMock(return_value=None)

    with patch("app.workers.publish_tasks.get_db_context", return_value=db_context):
        with patch(
            "app.workers.publish_tasks.create_publish_job_for_review_run",
            AsyncMock(return_value=job_id),
        ):
            with patch(
                "app.workers.publish_tasks.publish_review_run.delay",
            ) as delay_mock:
                publish_tasks.publish_for_review_run.run(str(uuid.uuid4()))

    delay_mock.assert_called_once_with(str(job_id))
    session.commit.assert_awaited_once()
