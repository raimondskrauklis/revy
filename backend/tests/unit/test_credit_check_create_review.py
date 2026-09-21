# backend/tests/unit/test_credit_check_create_review.py
"""Credit check in create_review_run — free plan gate at 25 completed runs."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.constants.enums import WorkspaceStatus
from app.core.exceptions import ForbiddenError
from app.models.workspaces import WorkspaceORM
from app.services.github_review import create_review_run


@pytest.fixture
def workspace_id():
    return uuid.uuid4()


def _workspace(*, completed: int, limit: int | None) -> WorkspaceORM:
    workspace = WorkspaceORM(
        slug="test",
        name="Test",
        status=WorkspaceStatus.active,
        review_run_limit=limit,
    )
    workspace.id = uuid.uuid4()
    workspace.completed_review_runs = completed
    return workspace


def _mock_settings(**overrides):
    """Mock settings — MagicMock with reviewer_llm_enabled() as method, others as properties."""
    from unittest.mock import MagicMock, PropertyMock
    mock = MagicMock()
    mock.reviewer_llm_enabled.return_value = True
    type(mock).embeddings_enabled = PropertyMock(return_value=True)
    type(mock).github_api_enabled = PropertyMock(return_value=True)
    for k, v in overrides.items():
        setattr(mock, k, v)
    return mock


@pytest.mark.asyncio
async def test_free_workspace_at_limit_raises_forbidden(workspace_id):
    """Free workspace at 25/25 should raise ForbiddenError with credit_limit_reached."""
    session = AsyncMock()
    workspace = _workspace(completed=25, limit=25)
    workspace.id = workspace_id
    session.get = AsyncMock(return_value=workspace)

    with (
        patch("app.services.github_review.settings", _mock_settings()),
        patch("app.services.github_review.ensure_revision_access", new_callable=AsyncMock),
    ):
        with pytest.raises(ForbiddenError) as exc:
            await create_review_run(
                session,
                workspace_id=workspace_id,
                repository_id=uuid.uuid4(),
                pull_request_id=uuid.uuid4(),
                revision_id=uuid.uuid4(),
            )

    assert exc.value.error_code == "credit_limit_reached"
    assert exc.value.details["completed_runs"] == 25
    assert exc.value.details["run_limit"] == 25


@pytest.mark.asyncio
async def test_free_workspace_below_limit_passes_credit_check(workspace_id):
    """Free workspace with 0/25 should pass credit check and hit next check."""
    session = AsyncMock()
    workspace = _workspace(completed=0, limit=25)
    workspace.id = workspace_id
    session.get = AsyncMock(return_value=workspace)

    with (
        patch("app.services.github_review.settings", _mock_settings()),
        patch("app.services.github_review.ensure_revision_access", new_callable=AsyncMock),
        patch(
            "app.services.github_review.index_job_in_progress",
            new_callable=AsyncMock,
            return_value=True,
        ),
    ):
        from app.core.exceptions import ConflictError

        with pytest.raises(ConflictError) as exc:
            await create_review_run(
                session,
                workspace_id=workspace_id,
                repository_id=uuid.uuid4(),
                pull_request_id=uuid.uuid4(),
                revision_id=uuid.uuid4(),
            )

        assert exc.value.error_code != "credit_limit_reached"


@pytest.mark.asyncio
async def test_pro_workspace_skips_credit_check(workspace_id):
    """Pro workspace (null limit) should skip credit check entirely."""
    session = AsyncMock()
    workspace = _workspace(completed=939, limit=None)
    workspace.id = workspace_id
    session.get = AsyncMock(return_value=workspace)

    with (
        patch("app.services.github_review.settings", _mock_settings()),
        patch("app.services.github_review.ensure_revision_access", new_callable=AsyncMock),
        patch(
            "app.services.github_review.index_job_in_progress",
            new_callable=AsyncMock,
            return_value=True,
        ),
    ):
        from app.core.exceptions import ConflictError

        with pytest.raises(ConflictError) as exc:
            await create_review_run(
                session,
                workspace_id=workspace_id,
                repository_id=uuid.uuid4(),
                pull_request_id=uuid.uuid4(),
                revision_id=uuid.uuid4(),
            )

        assert exc.value.error_code != "credit_limit_reached"


@pytest.mark.asyncio
async def test_workspace_not_found_raises_not_found(workspace_id):
    """Missing workspace should raise NotFoundError."""
    session = AsyncMock()
    session.get = AsyncMock(return_value=None)

    with (
        patch("app.services.github_review.settings", _mock_settings()),
        patch("app.services.github_review.ensure_revision_access", new_callable=AsyncMock),
    ):
        from app.core.exceptions import NotFoundError

        with pytest.raises(NotFoundError):
            await create_review_run(
                session,
                workspace_id=workspace_id,
                repository_id=uuid.uuid4(),
                pull_request_id=uuid.uuid4(),
                revision_id=uuid.uuid4(),
            )