# backend/app/services/github_pipeline_trace.py
"""GitHub pipeline trace capture and read API — review-quality O."""
from __future__ import annotations

import hashlib
import json
import time
from dataclasses import dataclass, field
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.constants.enums import (
    GitHubIndexJobStatus,
    GitHubPublishJobStatus,
    GitHubReviewRunStatus,
    PipelineArtifactKind,
    PipelineStepStatus,
    PipelineStepType,
    stored_enum_value,
)
from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.core.logging import get_logger
from app.integrations import github_api
from app.models.github_index_job import GitHubIndexJobORM
from app.models.github_installation import GitHubInstallationORM
from app.models.github_pipeline import (
    GitHubPipelineArtifactORM,
    GitHubPipelineRunORM,
    GitHubPipelineStepORM,
)
from app.models.github_publish_job import GitHubPublishJobORM
from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
from app.models.github_repository import GitHubRepositoryORM
from app.models.github_review_run import GitHubReviewRunORM
from app.schemas.github_pipeline import (
    PipelineArtifactResponse,
    PipelineRunResponse,
    PipelineStepResponse,
)
from app.services.github_indexing import ensure_revision_access

logger = get_logger(__name__)

_PROMPT_MAX_BYTES = 512 * 1024
_RAW_RESPONSE_MAX_BYTES = 512 * 1024


@dataclass
class StepTimer:
    started_at: float = field(default_factory=time.monotonic)

    def elapsed_ms(self) -> int:
        return int((time.monotonic() - self.started_at) * 1000)


def _hash_content(*, content_text: str | None, content_json: dict[str, Any] | None) -> str | None:
    if content_text is not None:
        payload = content_text.encode("utf-8")
    elif content_json is not None:
        payload = json.dumps(content_json, sort_keys=True, separators=(",", ":")).encode("utf-8")
    else:
        return None
    return hashlib.sha256(payload).hexdigest()


def _truncate_text(value: str, max_bytes: int) -> str:
    encoded = value.encode("utf-8")
    if len(encoded) <= max_bytes:
        return value
    return encoded[:max_bytes].decode("utf-8", errors="ignore")


async def get_pipeline_run_for_review_run(
    session: AsyncSession,
    *,
    review_run_id: UUID,
) -> GitHubPipelineRunORM | None:
    return await session.scalar(
        select(GitHubPipelineRunORM).where(GitHubPipelineRunORM.review_run_id == review_run_id)
    )


async def get_pipeline_run_for_index_job(
    session: AsyncSession,
    *,
    index_job_id: UUID,
) -> GitHubPipelineRunORM | None:
    return await session.scalar(
        select(GitHubPipelineRunORM).where(GitHubPipelineRunORM.index_job_id == index_job_id)
    )


async def ensure_pipeline_run_for_index_job(
    session: AsyncSession,
    *,
    job: GitHubIndexJobORM,
    head_sha: str,
) -> GitHubPipelineRunORM:
    existing = await get_pipeline_run_for_index_job(session, index_job_id=job.id)
    if existing is not None:
        return existing

    pipeline_run = GitHubPipelineRunORM(
        workspace_id=job.workspace_id,
        revision_id=job.revision_id,
        head_sha=head_sha,
        index_mode=job.index_mode,
        index_job_id=job.id,
    )
    session.add(pipeline_run)
    await session.flush()
    return pipeline_run


async def link_review_run_to_pipeline(
    session: AsyncSession,
    *,
    pipeline_run: GitHubPipelineRunORM,
    review_run_id: UUID,
) -> None:
    pipeline_run.review_run_id = review_run_id
    await session.flush()


async def link_publish_job_to_pipeline(
    session: AsyncSession,
    *,
    pipeline_run: GitHubPipelineRunORM,
    publish_job_id: UUID,
) -> None:
    pipeline_run.publish_job_id = publish_job_id
    await session.flush()


async def add_step_artifact(
    session: AsyncSession,
    *,
    step_id: UUID,
    kind: PipelineArtifactKind,
    content_text: str | None = None,
    content_json: dict[str, Any] | None = None,
) -> GitHubPipelineArtifactORM:
    artifact = GitHubPipelineArtifactORM(
        step_id=step_id,
        kind=kind,
        content_text=content_text,
        content_json=content_json,
        content_hash=_hash_content(content_text=content_text, content_json=content_json),
    )
    session.add(artifact)
    await session.flush()
    return artifact


async def _create_completed_step(
    session: AsyncSession,
    *,
    pipeline_run_id: UUID,
    step_type: PipelineStepType,
    duration_ms: int,
    status: PipelineStepStatus = PipelineStepStatus.completed,
    error: str | None = None,
    model_provider: str | None = None,
    model_id: str | None = None,
) -> GitHubPipelineStepORM:
    step = GitHubPipelineStepORM(
        pipeline_run_id=pipeline_run_id,
        step_type=step_type,
        status=status,
        duration_ms=duration_ms,
        error=error,
        model_provider=model_provider,
        model_id=model_id,
    )
    session.add(step)
    await session.flush()
    return step


async def _get_index_pipeline_step(
    session: AsyncSession,
    *,
    pipeline_run_id: UUID,
) -> GitHubPipelineStepORM | None:
    return await session.scalar(
        select(GitHubPipelineStepORM)
        .where(
            GitHubPipelineStepORM.pipeline_run_id == pipeline_run_id,
            GitHubPipelineStepORM.step_type == PipelineStepType.index,
        )
        .order_by(GitHubPipelineStepORM.created_at.asc())
        .limit(1)
    )


async def _get_step_manifest_artifact(
    session: AsyncSession,
    *,
    step_id: UUID,
) -> GitHubPipelineArtifactORM | None:
    return await session.scalar(
        select(GitHubPipelineArtifactORM)
        .where(
            GitHubPipelineArtifactORM.step_id == step_id,
            GitHubPipelineArtifactORM.kind == PipelineArtifactKind.manifest,
        )
        .order_by(GitHubPipelineArtifactORM.created_at.asc())
        .limit(1)
    )


async def pipeline_has_step(
    session: AsyncSession,
    *,
    pipeline_run_id: UUID,
    step_type: PipelineStepType,
) -> bool:
    step = await session.scalar(
        select(GitHubPipelineStepORM.id)
        .where(
            GitHubPipelineStepORM.pipeline_run_id == pipeline_run_id,
            GitHubPipelineStepORM.step_type == step_type,
        )
        .limit(1)
    )
    return step is not None


async def stash_pipeline_github_check_run_id(
    session: AsyncSession,
    *,
    pipeline_run_id: UUID,
    github_check_run_id: int,
) -> None:
    step = await _get_index_pipeline_step(session, pipeline_run_id=pipeline_run_id)
    if step is None:
        step = GitHubPipelineStepORM(
            pipeline_run_id=pipeline_run_id,
            step_type=PipelineStepType.index,
            status=PipelineStepStatus.pending,
            duration_ms=0,
        )
        session.add(step)
        await session.flush()

    manifest_artifact = await _get_step_manifest_artifact(session, step_id=step.id)
    manifest: dict[str, Any] = (
        dict(manifest_artifact.content_json)
        if manifest_artifact is not None and isinstance(manifest_artifact.content_json, dict)
        else {}
    )
    manifest["github_check_run_id"] = github_check_run_id
    if manifest_artifact is not None:
        manifest_artifact.content_json = manifest
    else:
        await add_step_artifact(
            session,
            step_id=step.id,
            kind=PipelineArtifactKind.manifest,
            content_json=manifest,
        )
    await session.flush()


async def finalize_pipeline_github_check_for_review_run(
    session: AsyncSession,
    *,
    review_run_id: UUID,
    summary: str,
) -> None:
    pipeline_run = await get_pipeline_run_for_review_run(session, review_run_id=review_run_id)
    if pipeline_run is None:
        return
    await finalize_pipeline_github_check_failure(
        session,
        pipeline_run_id=pipeline_run.id,
        summary=summary,
    )


async def finalize_pipeline_github_check_for_publish_job(
    session: AsyncSession,
    *,
    publish_job_id: UUID,
    summary: str,
) -> None:
    job = await session.get(GitHubPublishJobORM, publish_job_id)
    if job is None:
        return
    await finalize_pipeline_github_check_for_review_run(
        session,
        review_run_id=job.review_run_id,
        summary=summary,
    )


async def finalize_pipeline_github_check_for_index_job(
    session: AsyncSession,
    *,
    index_job_id: UUID,
    summary: str,
) -> None:
    pipeline_run = await get_pipeline_run_for_index_job(session, index_job_id=index_job_id)
    if pipeline_run is None:
        return
    await finalize_pipeline_github_check_failure(
        session,
        pipeline_run_id=pipeline_run.id,
        summary=summary,
    )

async def record_index_pipeline_step(
    session: AsyncSession,
    *,
    pipeline_run_id: UUID,
    job: GitHubIndexJobORM,
    duration_ms: int,
    github_check_run_id: int | None = None,
) -> None:
    status = (
        PipelineStepStatus.completed
        if job.status == GitHubIndexJobStatus.completed
        else PipelineStepStatus.failed
    )
    error = (
        (job.error_message or "index_failed")[:2000]
        if job.status == GitHubIndexJobStatus.failed
        else None
    )
    step = await _get_index_pipeline_step(session, pipeline_run_id=pipeline_run_id)
    if step is None:
        step = await _create_completed_step(
            session,
            pipeline_run_id=pipeline_run_id,
            step_type=PipelineStepType.index,
            duration_ms=duration_ms,
            status=status,
            error=error,
        )
    else:
        step.status = status
        step.duration_ms = duration_ms
        step.error = error
        await session.flush()

    manifest_artifact = await _get_step_manifest_artifact(session, step_id=step.id)
    manifest: dict[str, Any] = (
        dict(manifest_artifact.content_json)
        if manifest_artifact is not None and isinstance(manifest_artifact.content_json, dict)
        else {}
    )
    manifest.update(
        {
            "index_mode": stored_enum_value(job.index_mode),
            "chunk_count": job.chunk_count,
            "fallback_reason": job.fallback_reason,
            "warning_message": job.warning_message,
            "duration_ms": duration_ms,
        }
    )
    index_manifest_stats = getattr(job, "index_manifest_stats", None)
    if isinstance(index_manifest_stats, dict):
        for key in ("reused_count", "new_count", "embed_batches"):
            if key in index_manifest_stats:
                manifest[key] = index_manifest_stats[key]
    if github_check_run_id is not None:
        manifest["github_check_run_id"] = github_check_run_id
    if manifest_artifact is not None:
        manifest_artifact.content_json = manifest
    else:
        await add_step_artifact(
            session,
            step_id=step.id,
            kind=PipelineArtifactKind.manifest,
            content_json=manifest,
        )


async def record_retrieve_pipeline_step(
    session: AsyncSession,
    *,
    pipeline_run_id: UUID,
    manifest: dict[str, Any],
    duration_ms: int,
) -> None:
    step = await _create_completed_step(
        session,
        pipeline_run_id=pipeline_run_id,
        step_type=PipelineStepType.retrieve,
        duration_ms=duration_ms,
    )
    await add_step_artifact(
        session,
        step_id=step.id,
        kind=PipelineArtifactKind.manifest,
        content_json=manifest,
    )
    hits = manifest.get("retrieval_hits")
    if isinstance(hits, list) and hits:
        await add_step_artifact(
            session,
            step_id=step.id,
            kind=PipelineArtifactKind.retrieval_hits,
            content_json={"items": hits},
        )


async def record_review_pipeline_step(
    session: AsyncSession,
    *,
    pipeline_run_id: UUID,
    run: GitHubReviewRunORM,
    prompt: str,
    raw_response: str | None,
    parse_report: dict[str, Any],
    duration_ms: int,
) -> None:
    step = await _create_completed_step(
        session,
        pipeline_run_id=pipeline_run_id,
        step_type=PipelineStepType.review,
        duration_ms=duration_ms,
        status=(
            PipelineStepStatus.completed
            if run.status == GitHubReviewRunStatus.completed
            else PipelineStepStatus.failed
        ),
        error=(run.error_message or "review_failed")[:2000]
        if run.status == GitHubReviewRunStatus.failed
        else None,
        model_provider=run.provider,
        model_id=run.model_id,
    )
    await add_step_artifact(
        session,
        step_id=step.id,
        kind=PipelineArtifactKind.prompt,
        content_text=_truncate_text(prompt, _PROMPT_MAX_BYTES),
    )
    await add_step_artifact(
        session,
        step_id=step.id,
        kind=PipelineArtifactKind.raw_response,
        content_text=_truncate_text(raw_response or "", _RAW_RESPONSE_MAX_BYTES),
    )
    await add_step_artifact(
        session,
        step_id=step.id,
        kind=PipelineArtifactKind.parse_report,
        content_json=parse_report,
    )


async def record_reconcile_pipeline_step(
    session: AsyncSession,
    *,
    pipeline_run_id: UUID,
    group_count: int,
    duration_ms: int,
) -> None:
    step = await _create_completed_step(
        session,
        pipeline_run_id=pipeline_run_id,
        step_type=PipelineStepType.reconcile,
        duration_ms=duration_ms,
    )
    await add_step_artifact(
        session,
        step_id=step.id,
        kind=PipelineArtifactKind.manifest,
        content_json={"linked_group_count": group_count},
    )


async def record_judge_pipeline_step(
    session: AsyncSession,
    *,
    pipeline_run_id: UUID,
    judged_count: int,
    duration_ms: int,
) -> None:
    step = await _create_completed_step(
        session,
        pipeline_run_id=pipeline_run_id,
        step_type=PipelineStepType.judge,
        duration_ms=duration_ms,
    )
    await add_step_artifact(
        session,
        step_id=step.id,
        kind=PipelineArtifactKind.manifest,
        content_json={"judged_count": judged_count},
    )


async def record_publish_pipeline_step(
    session: AsyncSession,
    *,
    pipeline_run_id: UUID,
    job: GitHubPublishJobORM,
    summary_markdown: str,
    duration_ms: int,
) -> None:
    step = await _create_completed_step(
        session,
        pipeline_run_id=pipeline_run_id,
        step_type=PipelineStepType.publish,
        duration_ms=duration_ms,
        status=(
            PipelineStepStatus.completed
            if job.status == GitHubPublishJobStatus.completed
            else PipelineStepStatus.failed
        ),
        error=(job.error_message or "publish_failed")[:2000]
        if job.status == GitHubPublishJobStatus.failed
        else None,
    )
    await add_step_artifact(
        session,
        step_id=step.id,
        kind=PipelineArtifactKind.summary_markdown,
        content_text=summary_markdown,
    )


async def get_pipeline_trace_for_review_run(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    repository_id: UUID,
    pull_request_id: UUID,
    revision_id: UUID,
    review_run_id: UUID,
) -> PipelineRunResponse:
    await ensure_revision_access(
        session,
        workspace_id=workspace_id,
        repository_id=repository_id,
        pull_request_id=pull_request_id,
        revision_id=revision_id,
    )
    run = await session.get(GitHubReviewRunORM, review_run_id)
    if run is None or run.workspace_id != workspace_id or run.revision_id != revision_id:
        raise NotFoundError("Review run not found")

    pipeline_run = await session.scalar(
        select(GitHubPipelineRunORM)
        .where(
            GitHubPipelineRunORM.workspace_id == workspace_id,
            GitHubPipelineRunORM.review_run_id == review_run_id,
        )
        .options(
            selectinload(GitHubPipelineRunORM.steps).selectinload(GitHubPipelineStepORM.artifacts),
        )
    )
    if pipeline_run is None:
        raise NotFoundError("Pipeline trace not found")

    steps = sorted(pipeline_run.steps, key=lambda item: item.created_at)
    return PipelineRunResponse(
        id=pipeline_run.id,
        workspace_id=pipeline_run.workspace_id,
        revision_id=pipeline_run.revision_id,
        head_sha=pipeline_run.head_sha,
        index_mode=pipeline_run.index_mode,
        index_job_id=pipeline_run.index_job_id,
        review_run_id=pipeline_run.review_run_id,
        publish_job_id=pipeline_run.publish_job_id,
        created_at=pipeline_run.created_at,
        updated_at=pipeline_run.updated_at,
        steps=[
            PipelineStepResponse(
                id=step.id,
                step_type=step.step_type,
                status=step.status,
                duration_ms=step.duration_ms,
                model_provider=step.model_provider,
                model_id=step.model_id,
                input_tokens=step.input_tokens,
                output_tokens=step.output_tokens,
                error=step.error,
                created_at=step.created_at,
                updated_at=step.updated_at,
                artifacts=[
                    PipelineArtifactResponse.model_validate(artifact) for artifact in step.artifacts
                ],
            )
            for step in steps
        ],
    )


async def resolve_pipeline_github_check_run_id(
    session: AsyncSession,
    *,
    pipeline_run_id: UUID,
) -> int | None:
    step = await session.scalar(
        select(GitHubPipelineStepORM)
        .where(
            GitHubPipelineStepORM.pipeline_run_id == pipeline_run_id,
            GitHubPipelineStepORM.step_type == PipelineStepType.index,
        )
        .order_by(GitHubPipelineStepORM.created_at.asc())
        .limit(1)
    )
    if step is None:
        return None
    artifact = await session.scalar(
        select(GitHubPipelineArtifactORM)
        .where(
            GitHubPipelineArtifactORM.step_id == step.id,
            GitHubPipelineArtifactORM.kind == PipelineArtifactKind.manifest,
        )
        .order_by(GitHubPipelineArtifactORM.created_at.asc())
        .limit(1)
    )
    if artifact is None or not isinstance(artifact.content_json, dict):
        return None
    check_run_id = artifact.content_json.get("github_check_run_id")
    return check_run_id if isinstance(check_run_id, int) else None


async def start_pipeline_github_check(
    session: AsyncSession,
    *,
    pipeline_run: GitHubPipelineRunORM,
) -> int | None:
    if not settings.github_api_enabled:
        return None

    revision = await session.get(GitHubPullRequestRevisionORM, pipeline_run.revision_id)
    if revision is None:
        return None
    pull_request = await session.get(GitHubPullRequestORM, revision.pull_request_id)
    if pull_request is None:
        return None
    repository = await session.get(GitHubRepositoryORM, pull_request.repository_id)
    installation = await session.get(GitHubInstallationORM, pull_request.installation_id)
    if repository is None or installation is None:
        return None

    owner, repo_name = repository.full_name.split("/", 1)
    external_id = github_api.build_check_run_external_id(
        github_installation_id=installation.github_installation_id,
        github_pr_number=pull_request.number,
        head_sha=pipeline_run.head_sha,
    )
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            return await github_api.create_check_run(
                client,
                github_installation_id=installation.github_installation_id,
                owner=owner,
                repo=repo_name,
                head_sha=pipeline_run.head_sha,
                external_id=external_id,
                status="in_progress",
                summary="Revy review in progress…",
            )
    except httpx.HTTPError as exc:
        logger.warning(
            "pipeline_github_check_start_failed",
            extra={"pipeline_run_id": str(pipeline_run.id), "error": str(exc)},
        )
        return None


async def finalize_pipeline_github_check_failure(
    session: AsyncSession,
    *,
    pipeline_run_id: UUID,
    summary: str,
) -> None:
    check_run_id = await resolve_pipeline_github_check_run_id(session, pipeline_run_id=pipeline_run_id)
    if check_run_id is None or not settings.github_api_enabled:
        return

    pipeline_run = await session.get(GitHubPipelineRunORM, pipeline_run_id)
    if pipeline_run is None:
        return
    revision = await session.get(GitHubPullRequestRevisionORM, pipeline_run.revision_id)
    if revision is None:
        return
    pull_request = await session.get(GitHubPullRequestORM, revision.pull_request_id)
    if pull_request is None:
        return
    repository = await session.get(GitHubRepositoryORM, pull_request.repository_id)
    installation = await session.get(GitHubInstallationORM, pull_request.installation_id)
    if repository is None or installation is None:
        return

    owner, repo_name = repository.full_name.split("/", 1)
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            await github_api.update_check_run(
                client,
                github_installation_id=installation.github_installation_id,
                owner=owner,
                repo=repo_name,
                check_run_id=check_run_id,
                conclusion="failure",
                summary=summary,
            )
    except httpx.HTTPError as exc:
        logger.warning(
            "pipeline_github_check_finalize_failed",
            extra={"pipeline_run_id": str(pipeline_run_id), "error": str(exc)},
        )


async def purge_old_pipeline_artifacts(session: AsyncSession) -> int:
    retention_days = settings.pipeline_retention_days
    cutoff = datetime.now(UTC) - timedelta(days=retention_days)
    result = await session.execute(
        delete(GitHubPipelineRunORM).where(GitHubPipelineRunORM.created_at < cutoff)
    )
    deleted = int(result.rowcount or 0)
    logger.info(
        "pipeline_artifacts_purged",
        extra={"deleted_runs": deleted, "retention_days": retention_days},
    )
    return deleted
