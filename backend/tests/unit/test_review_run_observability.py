# backend/tests/unit/test_review_run_observability.py
"""Pipeline observability — review run observability helpers."""
import uuid
from contextlib import asynccontextmanager
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.constants.enums import GitHubReviewRunStatus
from app.services.review_run_observability import persist_review_run_permanent_failure


@pytest.mark.asyncio
async def test_persist_review_run_permanent_failure_commits():
    review_run_id = uuid.uuid4()
    run = MagicMock()
    run.status = GitHubReviewRunStatus.processing
    session = AsyncMock()
    session.get = AsyncMock(return_value=run)

    @asynccontextmanager
    async def fake_db_context():
        yield session

    with patch(
        "app.services.review_run_observability.get_db_context",
        fake_db_context,
    ):
        await persist_review_run_permanent_failure(
            review_run_id=review_run_id,
            error_message="provider down",
        )

    assert run.status == GitHubReviewRunStatus.failed
    assert run.error_message == "provider down"
    session.commit.assert_awaited_once()
