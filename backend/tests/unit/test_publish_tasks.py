# backend/tests/unit/test_publish_tasks.py
"""Publish Celery tasks — R6."""
import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

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
            "app.workers.publish_tasks.resolve_publish_job_id_for_review_run",
            AsyncMock(return_value=(job_id, True)),
        ):
            with patch(
                "app.workers.publish_tasks.dispatch_publish_review_run",
            ) as dispatch_mock:
                publish_tasks.publish_for_review_run.run(str(uuid.uuid4()))

    dispatch_mock.assert_called_once_with(str(job_id))
    session.commit.assert_awaited_once()


def test_publish_for_review_run_redispatches_existing_pending_job():
    existing_job_id = uuid.uuid4()

    session = AsyncMock()
    session.commit = AsyncMock()

    db_context = MagicMock()
    db_context.__aenter__ = AsyncMock(return_value=session)
    db_context.__aexit__ = AsyncMock(return_value=None)

    with patch("app.workers.publish_tasks.get_db_context", return_value=db_context):
        with patch(
            "app.workers.publish_tasks.resolve_publish_job_id_for_review_run",
            AsyncMock(return_value=(existing_job_id, False)),
        ):
            with patch(
                "app.workers.publish_tasks.dispatch_publish_review_run",
            ) as dispatch_mock:
                publish_tasks.publish_for_review_run.run(str(uuid.uuid4()))

    dispatch_mock.assert_called_once_with(str(existing_job_id))
    session.commit.assert_not_awaited()


def test_dispatch_publish_review_run_falls_back_to_inline_run():
    with patch(
        "app.workers.publish_tasks.publish_review_run.delay",
        side_effect=ConnectionError("broker down"),
    ):
        with patch("app.workers.publish_tasks.publish_review_run.run") as run_mock:
            publish_tasks.dispatch_publish_review_run("job-id")

    run_mock.assert_called_once_with("job-id")


@pytest.mark.asyncio
async def test_dispatch_publish_review_run_schedules_inline_when_loop_running():
    with patch(
        "app.workers.publish_tasks.publish_review_run.delay",
        side_effect=ConnectionError("broker down"),
    ):
        with patch("app.workers.publish_tasks.publish_review_run.run") as run_mock:
            with patch(
                "app.workers.publish_tasks._run_publish_review_run_inline",
                new_callable=AsyncMock,
            ) as inline_mock:
                publish_tasks.dispatch_publish_review_run("job-id")
                await asyncio.sleep(0)

    run_mock.assert_not_called()
    inline_mock.assert_awaited_once_with("job-id")


@pytest.mark.asyncio
async def test_run_publish_review_run_inline_marks_failed_on_cancelled():
    with patch(
        "app.workers.publish_tasks._execute_publish_review_run",
        AsyncMock(side_effect=asyncio.CancelledError()),
    ):
        with patch(
            "app.workers.publish_tasks._finalize_inline_publish_failure",
            new_callable=AsyncMock,
        ) as finalize_mock:
            with pytest.raises(asyncio.CancelledError):
                await publish_tasks._run_publish_review_run_inline("job-id")

    finalize_mock.assert_awaited_once_with("job-id", "inline publish cancelled")


@pytest.mark.asyncio
async def test_inline_publish_task_done_finalizes_uncaught_exception():
    with patch(
        "app.workers.publish_tasks._finalize_inline_publish_failure",
        new_callable=AsyncMock,
    ) as finalize_mock:

        async def failing() -> None:
            raise RuntimeError("boom")

        task = asyncio.create_task(failing())
        with pytest.raises(RuntimeError):
            await task

        publish_tasks._inline_publish_task_done("job-id", task)
        await asyncio.sleep(0)

    finalize_mock.assert_awaited_once_with("job-id", "inline publish failed: boom")
