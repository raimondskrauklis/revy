# backend/app/services/model_run_snapshot.py
"""Terminal pipeline model snapshot — model-run-capture MRC-P2."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.constants.enums import (
    PipelineArtifactKind,
    PipelineStepStatus,
    PipelineStepType,
    stored_enum_value,
)
from app.core.logging import get_logger
from app.models.github_llm_call_attempt import GitHubLlmCallAttemptORM
from app.models.github_pipeline import (
    GitHubPipelineRunORM,
    GitHubPipelineStepORM,
)

_SNAPSHOT_ROLE_BY_STEP: dict[PipelineStepType, str] = {
    PipelineStepType.index: "embedding",
    PipelineStepType.review: "reviewer",
    PipelineStepType.judge: "judge",
    PipelineStepType.publish: "publish",
}
_ATTEMPT_STEP_BY_ROLE: dict[str, str] = {
    "embedding": "index_embed",
    "reviewer": "review",
    "judge": "judge",
    "publish": "publish",
}

logger = get_logger(__name__)


@dataclass(frozen=True, slots=True)
class AttemptSnapshotInput:
    step_type: str
    provider: str | None
    request_model: str | None
    sequence: int = 0
    failure_class: str | None = None
    started: bool = True


@dataclass(frozen=True, slots=True)
class StepSnapshotInput:
    step_type: str
    status: str
    model_provider: str | None
    model_id: str | None
    manifest: dict[str, Any] | None = None
    sequence: int = 0


def _model_entry(
    *,
    provider: str | None,
    model_id: str | None,
    dimensions: int | None = None,
) -> dict[str, Any] | None:
    if not provider or not model_id:
        return None
    entry: dict[str, Any] = {"provider": provider, "model_id": model_id}
    if dimensions is not None:
        entry["dimensions"] = dimensions
    return entry


def _embedding_from_index(step: StepSnapshotInput) -> dict[str, Any] | None:
    manifest = step.manifest or {}
    if manifest.get("embedding_skipped_reason"):
        return None
    embed_batches = manifest.get("embed_batches", 0)
    if embed_batches == 0:
        return None
    embedding_model = manifest.get("embedding_model")
    if not isinstance(embedding_model, str) or not embedding_model:
        embedding_model = step.model_id
    if not isinstance(embedding_model, str) or not embedding_model:
        return None
    provider = manifest.get("embedding_provider") or step.model_provider
    model_id = embedding_model
    dimensions = manifest.get("embedding_dimensions")
    parsed_dimensions = dimensions if isinstance(dimensions, int) else None
    return _model_entry(
        provider=provider if isinstance(provider, str) else None,
        model_id=model_id if isinstance(model_id, str) else None,
        dimensions=parsed_dimensions,
    )


def _role_entry_from_step(role: str, step: StepSnapshotInput) -> dict[str, Any] | None:
    if role == "embedding":
        return _embedding_from_index(step)
    return _model_entry(provider=step.model_provider, model_id=step.model_id)


def _step_status_rank(status: str) -> int:
    if status == PipelineStepStatus.completed.value:
        return 2
    if status == PipelineStepStatus.failed.value:
        return 1
    return 0


def _pick_terminal_step(candidates: list[StepSnapshotInput]) -> StepSnapshotInput | None:
    if not candidates:
        return None
    return max(candidates, key=lambda step: (_step_status_rank(step.status), step.sequence))


def _pick_terminal_attempt(candidates: list[AttemptSnapshotInput]) -> AttemptSnapshotInput | None:
    if not candidates:
        return None
    started = [attempt for attempt in candidates if attempt.started]
    pool = started if started else candidates

    def _attempt_rank(attempt: AttemptSnapshotInput) -> tuple[int, int]:
        succeeded = 1 if attempt.failure_class is None else 0
        return (succeeded, attempt.sequence)

    return max(pool, key=_attempt_rank)


def _attempt_fallback(
    attempts: list[AttemptSnapshotInput],
    *,
    role: str,
) -> dict[str, Any] | None:
    attempt_step_type = _ATTEMPT_STEP_BY_ROLE.get(role, role)
    matching = [attempt for attempt in attempts if attempt.step_type == attempt_step_type]
    selected = _pick_terminal_attempt(matching)
    if selected is None:
        return None
    return _model_entry(
        provider=selected.provider,
        model_id=selected.request_model,
    )


def _embedding_step_skipped(step: StepSnapshotInput) -> bool:
    manifest = step.manifest or {}
    if manifest.get("embedding_skipped_reason"):
        return True
    return manifest.get("embed_batches") == 0


def build_models_snapshot(
    steps: list[StepSnapshotInput],
    *,
    attempts: list[AttemptSnapshotInput] | None = None,
) -> dict[str, Any]:
    """Build terminal models snapshot from pipeline steps and optional attempt fallbacks."""
    attempt_rows = attempts or []
    snapshot: dict[str, Any] = {}
    steps_by_type: dict[str, list[StepSnapshotInput]] = {}
    for step in steps:
        if step.status not in (
            PipelineStepStatus.completed.value,
            PipelineStepStatus.failed.value,
        ):
            continue
        steps_by_type.setdefault(step.step_type, []).append(step)

    for step_type, role in _SNAPSHOT_ROLE_BY_STEP.items():
        step = _pick_terminal_step(steps_by_type.get(step_type.value, []))
        entry: dict[str, Any] | None = None
        skip_attempt_fallback = False
        if step is not None:
            entry = _role_entry_from_step(role, step)
            if role == "embedding" and entry is None and _embedding_step_skipped(step):
                skip_attempt_fallback = True
        if entry is None and not skip_attempt_fallback:
            entry = _attempt_fallback(attempt_rows, role=role)
        if entry is not None:
            snapshot[role] = entry
    return snapshot


def _step_manifest(step: GitHubPipelineStepORM) -> dict[str, Any] | None:
    for artifact in step.artifacts:
        if artifact.kind != PipelineArtifactKind.manifest:
            continue
        if isinstance(artifact.content_json, dict):
            return artifact.content_json
    return None


def _step_inputs(steps: list[GitHubPipelineStepORM]) -> list[StepSnapshotInput]:
    ordered = sorted(steps, key=lambda step: step.created_at)
    return [
        StepSnapshotInput(
            step_type=stored_enum_value(step.step_type),
            status=stored_enum_value(step.status),
            model_provider=step.model_provider,
            model_id=step.model_id,
            manifest=_step_manifest(step),
            sequence=index,
        )
        for index, step in enumerate(ordered)
    ]


def _attempt_inputs(attempts: list[GitHubLlmCallAttemptORM]) -> list[AttemptSnapshotInput]:
    ordered = sorted(
        attempts,
        key=lambda attempt: (attempt.started_at is None, attempt.started_at),
    )
    return [
        AttemptSnapshotInput(
            step_type=stored_enum_value(attempt.step_type),
            provider=attempt.provider,
            request_model=attempt.request_model,
            sequence=index,
            failure_class=(
                stored_enum_value(attempt.failure_class)
                if attempt.failure_class is not None
                else None
            ),
            started=attempt.started_at is not None,
        )
        for index, attempt in enumerate(ordered)
    ]


async def persist_models_snapshot(
    session: AsyncSession,
    *,
    pipeline_run_id: UUID,
) -> dict[str, Any] | None:
    """Write `github_pipeline_runs.models_snapshot` from completed pipeline steps."""
    return await _write_models_snapshot(session, pipeline_run_id=pipeline_run_id)


async def _write_models_snapshot(
    session: AsyncSession,
    *,
    pipeline_run_id: UUID,
) -> dict[str, Any] | None:
    pipeline_run = await session.scalar(
        select(GitHubPipelineRunORM)
        .where(GitHubPipelineRunORM.id == pipeline_run_id)
        .options(
            selectinload(GitHubPipelineRunORM.steps).selectinload(
                GitHubPipelineStepORM.artifacts
            ),
        )
    )
    if pipeline_run is None:
        return None

    attempt_rows = list(
        await session.scalars(
            select(GitHubLlmCallAttemptORM)
            .where(GitHubLlmCallAttemptORM.pipeline_run_id == pipeline_run_id)
            .order_by(GitHubLlmCallAttemptORM.started_at.asc())
        )
    )
    snapshot = build_models_snapshot(
        _step_inputs(list(pipeline_run.steps)),
        attempts=_attempt_inputs(attempt_rows),
    )
    pipeline_run.models_snapshot = snapshot or None
    await session.flush()
    return snapshot


async def try_persist_models_snapshot(
    session: AsyncSession,
    *,
    pipeline_run_id: UUID,
) -> None:
    """Best-effort snapshot write — must not block terminal pipeline hooks."""
    try:
        async with session.begin_nested():
            await _write_models_snapshot(session, pipeline_run_id=pipeline_run_id)
    except Exception:
        logger.warning(
            "models_snapshot_persist_failed",
            exc_info=True,
            extra={"pipeline_run_id": str(pipeline_run_id)},
        )
