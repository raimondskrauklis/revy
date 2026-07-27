# backend/tests/unit/test_pipeline_purge_tasks.py
"""Pipeline purge Celery task — review-quality RQ3."""
from unittest.mock import patch

from app.workers.pipeline_purge_tasks import purge_old_pipeline_artifacts_task


def test_purge_old_pipeline_artifacts_task_runs():
    with patch(
        "app.workers.async_runner.run_worker_async",
        return_value=4,
    ):
        result = purge_old_pipeline_artifacts_task.run()

    assert result == 4
