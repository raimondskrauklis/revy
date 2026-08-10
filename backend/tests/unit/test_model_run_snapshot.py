# backend/tests/unit/test_model_run_snapshot.py
"""Model run snapshot builder and terminal writer — MRC-P2."""
from __future__ import annotations

from datetime import UTC, datetime
from unittest.mock import AsyncMock, MagicMock
from uuid import uuid4

import pytest
from sqlalchemy.exc import SQLAlchemyError

from app.constants.enums import PipelineArtifactKind, PipelineStepStatus, PipelineStepType
from app.services.model_run_snapshot import (
    AttemptSnapshotInput,
    StepSnapshotInput,
    build_models_snapshot,
    persist_models_snapshot,
    try_persist_models_snapshot,
)


def test_build_models_snapshot_full_pipeline():
    snapshot = build_models_snapshot(
        [
            StepSnapshotInput(
                step_type=PipelineStepType.index.value,
                status=PipelineStepStatus.completed.value,
                model_provider="voyage",
                model_id="voyage-code-3.5",
                manifest={
                    "embed_batches": 1,
                    "embedding_provider": "voyage",
                    "embedding_model": "voyage-code-3.5",
                    "embedding_dimensions": 1024,
                },
            ),
            StepSnapshotInput(
                step_type=PipelineStepType.review.value,
                status=PipelineStepStatus.completed.value,
                model_provider="moonshot",
                model_id="kimi-k2.7-code",
            ),
            StepSnapshotInput(
                step_type=PipelineStepType.judge.value,
                status=PipelineStepStatus.completed.value,
                model_provider="anthropic",
                model_id="claude-sonnet-5",
            ),
            StepSnapshotInput(
                step_type=PipelineStepType.publish.value,
                status=PipelineStepStatus.completed.value,
                model_provider="moonshot",
                model_id="kimi-k2.7-code",
            ),
        ]
    )
    assert snapshot == {
        "embedding": {
            "provider": "voyage",
            "model_id": "voyage-code-3.5",
            "dimensions": 1024,
        },
        "reviewer": {"provider": "moonshot", "model_id": "kimi-k2.7-code"},
        "judge": {"provider": "anthropic", "model_id": "claude-sonnet-5"},
        "publish": {"provider": "moonshot", "model_id": "kimi-k2.7-code"},
    }


def test_build_models_snapshot_reuse_only_index_omits_embedding():
    snapshot = build_models_snapshot(
        [
            StepSnapshotInput(
                step_type=PipelineStepType.index.value,
                status=PipelineStepStatus.completed.value,
                model_provider=None,
                model_id=None,
                manifest={
                    "embed_batches": 0,
                    "embedding_skipped_reason": "reused_chunks_only",
                },
            ),
            StepSnapshotInput(
                step_type=PipelineStepType.review.value,
                status=PipelineStepStatus.completed.value,
                model_provider="moonshot",
                model_id="kimi-k2.7-code",
            ),
        ]
    )
    assert "embedding" not in snapshot
    assert snapshot["reviewer"]["model_id"] == "kimi-k2.7-code"


def test_build_models_snapshot_reuse_with_stray_embedding_model_omits_embedding():
    snapshot = build_models_snapshot(
        [
            StepSnapshotInput(
                step_type=PipelineStepType.index.value,
                status=PipelineStepStatus.completed.value,
                model_provider="voyage",
                model_id="voyage-code-3.5",
                manifest={
                    "embed_batches": 0,
                    "embedding_model": "voyage-code-3.5",
                },
            ),
        ]
    )
    assert "embedding" not in snapshot


def test_build_models_snapshot_missing_manifest_uses_attempt_fallback():
    snapshot = build_models_snapshot(
        [
            StepSnapshotInput(
                step_type=PipelineStepType.index.value,
                status=PipelineStepStatus.completed.value,
                model_provider=None,
                model_id=None,
                manifest=None,
            ),
        ],
        attempts=[
            AttemptSnapshotInput(
                step_type="index_embed",
                provider="voyage",
                request_model="voyage-code-3.5",
            ),
        ],
    )
    assert snapshot["embedding"]["model_id"] == "voyage-code-3.5"


def test_build_models_snapshot_embedding_falls_back_to_step_model_id():
    snapshot = build_models_snapshot(
        [
            StepSnapshotInput(
                step_type=PipelineStepType.index.value,
                status=PipelineStepStatus.completed.value,
                model_provider="voyage",
                model_id="voyage-code-3.5",
                manifest={"embed_batches": 1},
            ),
        ]
    )
    assert snapshot["embedding"] == {
        "provider": "voyage",
        "model_id": "voyage-code-3.5",
    }


def test_build_models_snapshot_skipped_embedding_ignores_attempt_fallback():
    snapshot = build_models_snapshot(
        [
            StepSnapshotInput(
                step_type=PipelineStepType.index.value,
                status=PipelineStepStatus.completed.value,
                model_provider=None,
                model_id=None,
                manifest={
                    "embed_batches": 0,
                    "embedding_skipped_reason": "reused_chunks_only",
                },
            ),
        ],
        attempts=[
            AttemptSnapshotInput(
                step_type="index_embed",
                provider="voyage",
                request_model="voyage-code-3.5",
            ),
        ],
    )
    assert "embedding" not in snapshot


def test_build_models_snapshot_attempt_fallback_for_embedding():
    snapshot = build_models_snapshot(
        [
            StepSnapshotInput(
                step_type=PipelineStepType.index.value,
                status=PipelineStepStatus.completed.value,
                model_provider=None,
                model_id=None,
                manifest={"embed_batches": 1},
            ),
        ],
        attempts=[
            AttemptSnapshotInput(
                step_type="index_embed",
                provider="voyage",
                request_model="voyage-code-3.5",
            ),
        ],
    )
    assert snapshot["embedding"] == {
        "provider": "voyage",
        "model_id": "voyage-code-3.5",
    }


def test_build_models_snapshot_partial_run_only_completed_stages():
    snapshot = build_models_snapshot(
        [
            StepSnapshotInput(
                step_type=PipelineStepType.index.value,
                status=PipelineStepStatus.completed.value,
                model_provider="voyage",
                model_id="voyage-code-3.5",
                manifest={
                    "embed_batches": 1,
                    "embedding_model": "voyage-code-3.5",
                },
            ),
            StepSnapshotInput(
                step_type=PipelineStepType.review.value,
                status=PipelineStepStatus.failed.value,
                model_provider="moonshot",
                model_id="kimi-k2.7-code",
            ),
            StepSnapshotInput(
                step_type=PipelineStepType.publish.value,
                status=PipelineStepStatus.pending.value,
                model_provider=None,
                model_id=None,
            ),
        ]
    )
    assert "embedding" in snapshot
    assert snapshot["reviewer"]["model_id"] == "kimi-k2.7-code"
    assert "publish" not in snapshot


def test_build_models_snapshot_prefers_latest_completed_step():
    snapshot = build_models_snapshot(
        [
            StepSnapshotInput(
                step_type=PipelineStepType.review.value,
                status=PipelineStepStatus.failed.value,
                model_provider="moonshot",
                model_id="kimi-old",
                sequence=0,
            ),
            StepSnapshotInput(
                step_type=PipelineStepType.review.value,
                status=PipelineStepStatus.completed.value,
                model_provider="moonshot",
                model_id="kimi-k2.7-code",
                sequence=1,
            ),
        ]
    )
    assert snapshot["reviewer"]["model_id"] == "kimi-k2.7-code"


def test_build_models_snapshot_attempt_fallback_prefers_successful_latest():
    snapshot = build_models_snapshot(
        [],
        attempts=[
            AttemptSnapshotInput(
                step_type="review",
                provider="moonshot",
                request_model="kimi-old",
                sequence=0,
                failure_class="timeout",
            ),
            AttemptSnapshotInput(
                step_type="review",
                provider="moonshot",
                request_model="kimi-k2.7-code",
                sequence=1,
                failure_class=None,
            ),
        ],
    )
    assert snapshot["reviewer"]["model_id"] == "kimi-k2.7-code"


def test_build_models_snapshot_attempt_fallback_prefers_started_attempt():
    snapshot = build_models_snapshot(
        [],
        attempts=[
            AttemptSnapshotInput(
                step_type="review",
                provider="moonshot",
                request_model="kimi-stale",
                sequence=1,
                failure_class="timeout",
                started=False,
            ),
            AttemptSnapshotInput(
                step_type="review",
                provider="moonshot",
                request_model="kimi-k2.7-code",
                sequence=0,
                failure_class="timeout",
                started=True,
            ),
        ],
    )
    assert snapshot["reviewer"]["model_id"] == "kimi-k2.7-code"


@pytest.mark.asyncio
async def test_persist_models_snapshot_writes_pipeline_run():
    pipeline_run_id = uuid4()
    manifest_artifact = MagicMock(
        kind=PipelineArtifactKind.manifest,
        content_json={
            "embed_batches": 1,
            "embedding_provider": "voyage",
            "embedding_model": "voyage-code-3.5",
            "embedding_dimensions": 1024,
        },
    )
    index_step = MagicMock(
        step_type=PipelineStepType.index,
        status=PipelineStepStatus.completed,
        model_provider="voyage",
        model_id="voyage-code-3.5",
        artifacts=[manifest_artifact],
        created_at=datetime(2026, 8, 10, 12, 0, tzinfo=UTC),
    )
    review_step = MagicMock(
        step_type=PipelineStepType.review,
        status=PipelineStepStatus.completed,
        model_provider="moonshot",
        model_id="kimi-k2.7-code",
        artifacts=[],
        created_at=datetime(2026, 8, 10, 12, 1, tzinfo=UTC),
    )
    pipeline_run = MagicMock(id=pipeline_run_id, steps=[index_step, review_step], models_snapshot=None)

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=pipeline_run)
    session.scalars = AsyncMock(return_value=MagicMock(__iter__=lambda self: iter([])))
    session.flush = AsyncMock()

    snapshot = await persist_models_snapshot(session, pipeline_run_id=pipeline_run_id)

    assert snapshot is not None
    assert snapshot["embedding"]["model_id"] == "voyage-code-3.5"
    assert snapshot["reviewer"]["model_id"] == "kimi-k2.7-code"
    assert pipeline_run.models_snapshot == snapshot
    session.flush.assert_awaited_once()


@pytest.mark.asyncio
async def test_try_persist_models_snapshot_swallows_type_error():
    nested = MagicMock()
    nested.__aenter__ = AsyncMock(return_value=None)
    nested.__aexit__ = AsyncMock(return_value=None)

    session = AsyncMock()
    session.begin_nested = MagicMock(return_value=nested)
    session.scalar = AsyncMock(side_effect=TypeError("unexpected orm state"))

    await try_persist_models_snapshot(session, pipeline_run_id=uuid4())


@pytest.mark.asyncio
async def test_try_persist_models_snapshot_swallows_write_error():
    nested = MagicMock()
    nested.__aenter__ = AsyncMock(return_value=None)
    nested.__aexit__ = AsyncMock(return_value=None)

    session = AsyncMock()
    session.begin_nested = MagicMock(return_value=nested)
    session.scalar = AsyncMock(side_effect=SQLAlchemyError("write failed"))

    await try_persist_models_snapshot(session, pipeline_run_id=uuid4())
