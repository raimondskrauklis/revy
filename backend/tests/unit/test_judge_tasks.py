# backend/tests/unit/test_judge_tasks.py
"""Judge Celery tasks — R5."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

from app.workers import judge_tasks


def test_judge_review_run_task_runs():
    review_run_id = uuid.uuid4()

    session = AsyncMock()
    session.commit = AsyncMock()

    db_context = MagicMock()
    db_context.__aenter__ = AsyncMock(return_value=session)
    db_context.__aexit__ = AsyncMock(return_value=None)

    with patch("app.workers.judge_tasks.get_db_context", return_value=db_context):
        with patch(
            "app.workers.judge_tasks.run_judge_for_review_run",
            AsyncMock(return_value=(1, None)),
        ) as judge_mock:
            judge_tasks.judge_review_run.run(str(review_run_id))

    judge_mock.assert_awaited_once()
    session.commit.assert_awaited_once()
