# backend/tests/unit/test_index_tasks.py
"""Indexing Celery tasks — R3."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.constants.enums import GitHubIndexJobStatus
from app.models.github_index_job import GitHubIndexJobORM
from app.workers import index_tasks


def test_index_pull_request_revision_runs_job():
    job = GitHubIndexJobORM(
        revision_id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        status=GitHubIndexJobStatus.completed,
        chunk_count=3,
    )
    job.id = uuid.uuid4()

    session = AsyncMock()

    db_context = MagicMock()
    db_context.__aenter__ = AsyncMock(return_value=session)
    db_context.__aexit__ = AsyncMock(return_value=None)

    with patch("app.workers.index_tasks.get_db_context", return_value=db_context):
        with patch(
            "app.workers.index_tasks.run_index_job",
            AsyncMock(return_value=job),
        ) as run_mock:
            index_tasks.index_pull_request_revision.run(str(job.id))

    run_mock.assert_awaited_once()
