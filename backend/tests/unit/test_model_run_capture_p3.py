# backend/tests/unit/test_model_run_capture_p3.py
"""Model run capture API exposure — MRC-P3."""
from __future__ import annotations

import uuid
from datetime import UTC, datetime

import pytest

from app.constants.enums import (
    GitHubIndexMode,
    PipelineArtifactKind,
    PipelineStepStatus,
    PipelineStepType,
)
from app.models.github_pipeline import GitHubPipelineArtifactORM, GitHubPipelineStepORM
from app.schemas.github_pipeline import (
    ModelsSnapshotResponse,
    PipelineRunResponse,
    PipelineStepResponse,
)


def test_build_pipeline_run_response_maps_models_snapshot():
    from app.models.github_pipeline import GitHubPipelineRunORM
    from app.services.github_pipeline_trace import build_pipeline_run_response

    models_snapshot = {
        "embedding": {"provider": "voyage", "model_id": "voyage-code-3.5"},
        "reviewer": None,
        "judge": None,
        "publish": None,
    }
    pipeline_run = GitHubPipelineRunORM(
        workspace_id=uuid.uuid4(),
        revision_id=uuid.uuid4(),
        head_sha="abc",
        index_mode=GitHubIndexMode.diff,
    )
    pipeline_run.id = uuid.uuid4()
    pipeline_run.models_snapshot = models_snapshot
    pipeline_run.created_at = datetime.now(UTC)
    pipeline_run.updated_at = datetime.now(UTC)
    pipeline_run.steps = []

    response = build_pipeline_run_response(pipeline_run)

    assert response.models_snapshot == ModelsSnapshotResponse.model_validate(models_snapshot)


def test_pipeline_run_response_models_snapshot_round_trip():
    snapshot = {
        "embedding": {"provider": "voyage", "model_id": "voyage-code-3.5", "dimensions": 1024},
        "reviewer": {"provider": "moonshot", "model_id": "kimi-k2.7-code"},
        "judge": None,
        "publish": {"provider": "moonshot", "model_id": "kimi-k2.7-code"},
    }
    response = PipelineRunResponse(
        id=uuid.uuid4(),
        workspace_id=uuid.uuid4(),
        revision_id=uuid.uuid4(),
        head_sha="abc123",
        index_mode=GitHubIndexMode.diff,
        models_snapshot=ModelsSnapshotResponse.model_validate(snapshot),
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    dumped = response.model_dump(mode="json")
    assert dumped["models_snapshot"]["embedding"]["model_id"] == "voyage-code-3.5"
    assert dumped["models_snapshot"]["judge"] is None


def test_pipeline_step_response_index_embedding_fields():
    response = PipelineStepResponse(
        id=uuid.uuid4(),
        step_type=PipelineStepType.index,
        status=PipelineStepStatus.completed,
        embedding_model="voyage-code-3.5",
        embedding_dimensions=1024,
        created_at=datetime.now(UTC),
        updated_at=datetime.now(UTC),
    )
    dumped = response.model_dump(mode="json")
    assert dumped["embedding_model"] == "voyage-code-3.5"
    assert dumped["embedding_dimensions"] == 1024
    assert dumped["embedding_skipped_reason"] is None


def test_pipeline_step_response_from_orm_defaults_embedding_fields():
    step = GitHubPipelineStepORM(
        pipeline_run_id=uuid.uuid4(),
        step_type=PipelineStepType.review,
        status=PipelineStepStatus.completed,
    )
    step.id = uuid.uuid4()
    step.created_at = datetime.now(UTC)
    step.updated_at = datetime.now(UTC)
    step.artifacts = []

    response = PipelineStepResponse.model_validate(step)

    assert response.embedding_model is None
    assert response.embedding_dimensions is None
    assert response.embedding_skipped_reason is None


def test_index_embedding_manifest_fields_rejects_bool_dimensions():
    from app.models.github_pipeline import GitHubPipelineStepORM
    from app.services.github_pipeline_trace import _index_embedding_manifest_fields

    step = GitHubPipelineStepORM(
        pipeline_run_id=uuid.uuid4(),
        step_type=PipelineStepType.index,
        status=PipelineStepStatus.completed,
    )
    step.id = uuid.uuid4()
    step.artifacts = [
        GitHubPipelineArtifactORM(
            step_id=step.id,
            kind=PipelineArtifactKind.manifest,
            content_json={"embedding_dimensions": True},
        )
    ]

    fields = _index_embedding_manifest_fields(step)

    assert fields["embedding_dimensions"] is None


@pytest.mark.asyncio
async def test_get_pipeline_trace_exposes_models_snapshot_and_index_manifest():
    from unittest.mock import AsyncMock, patch

    from app.constants.enums import GitHubReviewRunStatus, ReviewProfile
    from app.models.github_pipeline import GitHubPipelineRunORM
    from app.models.github_review_run import GitHubReviewRunORM
    from app.services.github_pipeline_trace import get_pipeline_trace_for_review_run

    workspace_id = uuid.uuid4()
    repository_id = uuid.uuid4()
    pull_request_id = uuid.uuid4()
    revision_id = uuid.uuid4()
    review_run_id = uuid.uuid4()
    pipeline_run_id = uuid.uuid4()
    index_step_id = uuid.uuid4()

    run = GitHubReviewRunORM(
        revision_id=revision_id,
        workspace_id=workspace_id,
        status=GitHubReviewRunStatus.completed,
        profile=ReviewProfile.standard,
        provider="moonshot",
    )
    run.id = review_run_id

    models_snapshot = {
        "embedding": {"provider": "voyage", "model_id": "voyage-code-3.5", "dimensions": 1024},
        "reviewer": {"provider": "moonshot", "model_id": "kimi-k2.7-code"},
        "judge": None,
        "publish": None,
    }
    pipeline_run = GitHubPipelineRunORM(
        workspace_id=workspace_id,
        revision_id=revision_id,
        head_sha="abc",
        index_mode=GitHubIndexMode.diff,
        review_run_id=review_run_id,
    )
    pipeline_run.id = pipeline_run_id
    pipeline_run.models_snapshot = models_snapshot
    pipeline_run.created_at = datetime.now(UTC)
    pipeline_run.updated_at = datetime.now(UTC)

    index_step = GitHubPipelineStepORM(
        pipeline_run_id=pipeline_run_id,
        step_type=PipelineStepType.index,
        status=PipelineStepStatus.completed,
        duration_ms=50,
        model_provider="voyage",
        model_id="voyage-code-3.5",
    )
    index_step.id = index_step_id
    index_step.created_at = datetime.now(UTC)
    index_step.updated_at = datetime.now(UTC)
    index_step.artifacts = [
        GitHubPipelineArtifactORM(
            step_id=index_step_id,
            kind=PipelineArtifactKind.manifest,
            content_json={
                "embed_batches": 1,
                "embedding_model": "voyage-code-3.5",
                "embedding_dimensions": 1024,
            },
        )
    ]
    index_step.artifacts[0].id = uuid.uuid4()
    index_step.artifacts[0].created_at = datetime.now(UTC)
    pipeline_run.steps = [index_step]

    session = AsyncMock()
    session.get = AsyncMock(return_value=run)
    session.scalar = AsyncMock(return_value=pipeline_run)

    with patch(
        "app.services.github_pipeline_trace.ensure_revision_access",
        AsyncMock(),
    ):
        response = await get_pipeline_trace_for_review_run(
            session,
            workspace_id=workspace_id,
            repository_id=repository_id,
            pull_request_id=pull_request_id,
            revision_id=revision_id,
            review_run_id=review_run_id,
        )

    assert response.models_snapshot == ModelsSnapshotResponse.model_validate(models_snapshot)
    assert response.steps[0].embedding_model == "voyage-code-3.5"
    assert response.steps[0].embedding_dimensions == 1024


@pytest.mark.asyncio
async def test_build_pipeline_run_response_invalid_snapshot_returns_none():
    from app.models.github_pipeline import GitHubPipelineRunORM
    from app.services.github_pipeline_trace import build_pipeline_run_response

    pipeline_run = GitHubPipelineRunORM(
        workspace_id=uuid.uuid4(),
        revision_id=uuid.uuid4(),
        head_sha="abc",
        index_mode=GitHubIndexMode.diff,
    )
    pipeline_run.id = uuid.uuid4()
    pipeline_run.models_snapshot = {"embedding": "not-a-role-object"}
    pipeline_run.created_at = datetime.now(UTC)
    pipeline_run.updated_at = datetime.now(UTC)
    pipeline_run.steps = []

    response = build_pipeline_run_response(pipeline_run)

    assert response.models_snapshot is None
