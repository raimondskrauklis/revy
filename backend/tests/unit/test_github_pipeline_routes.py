# backend/tests/unit/test_github_pipeline_routes.py
"""Pipeline trace routes — review-quality RQ3."""
import uuid
from datetime import UTC, datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.api.v1.workspaces.installation_review import get_review_run_pipeline
from app.constants.enums import GitHubIndexMode, PipelineStepType
from app.schemas.github_pipeline import PipelineRunResponse, PipelineStepResponse


@pytest.mark.asyncio
async def test_get_review_run_pipeline_returns_trace():
    workspace_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    review_run_id = uuid.uuid4()
    session = AsyncMock()
    current_user = AsyncMock()
    current_user.workspace_id = workspace_id

    pipeline = PipelineRunResponse(
        id=uuid.uuid4(),
        workspace_id=workspace_id,
        revision_id=revision_id,
        head_sha="abc",
        index_mode=GitHubIndexMode.diff,
        review_run_id=review_run_id,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
        steps=[
            PipelineStepResponse(
                id=uuid.uuid4(),
                step_type=PipelineStepType.retrieve,
                status="completed",
                duration_ms=50,
                created_at=datetime.now(UTC),
                updated_at=datetime.now(UTC),
                artifacts=[],
            )
        ],
    )

    with patch("app.api.v1.workspaces.installation_review.require_permission"):
        with patch("app.api.v1.workspaces.installation_review.require_same_workspace"):
            with patch(
                "app.api.v1.workspaces.installation_review.get_pipeline_trace_for_review_run",
                AsyncMock(return_value=pipeline),
            ):
                response = await get_review_run_pipeline(
                    workspace_id=workspace_id,
                    repository_id=repository_id,
                    pull_request_id=pull_request_id,
                    revision_id=revision_id,
                    review_run_id=review_run_id,
                    current_user=current_user,
                    session=session,
                )

    assert response.data.review_run_id == review_run_id
    assert response.data.steps[0].step_type == PipelineStepType.retrieve
