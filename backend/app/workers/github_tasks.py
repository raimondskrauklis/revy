# backend/app/workers/github_tasks.py
"""GitHub webhook Celery tasks — github_events queue.

Synchronize autostart contract: ``apply_resolution_for_synchronize`` runs pairing
for the webhook revision, then enqueues the pending index job (or schedules
coalesced autostart). The review pipeline does not start until pairing finishes.
"""
from __future__ import annotations

from datetime import UTC, datetime, timedelta
from uuid import UUID

from celery.exceptions import Retry
from sqlalchemy import select

from app.constants.enums import GitHubIndexJobTriggerSource
from app.core.config import settings
from app.core.database import get_db_context
from app.core.logging import get_logger
from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
from app.models.github_webhook_delivery import GitHubWebhookDeliveryORM
from app.services.github_generation_lifecycle import (
    is_authoritative_for_pull_request_head,
    supersede_active_generations_for_revision,
)
from app.services.github_indexing import (
    enqueue_index_job,
    fail_pending_index_job_for_resolution_error,
)
from app.services.github_installations import apply_installation_webhook_event
from app.services.github_pipeline_trace import finalize_pipeline_github_check_for_index_job
from app.services.github_pull_requests import (
    apply_issue_comment_webhook_event,
    apply_pull_request_review_webhook_event,
    apply_pull_request_webhook_event,
)
from app.services.github_repositories import apply_installation_repositories_webhook_event
from app.services.github_resolution_metrics import apply_resolution_status_for_synchronize
from app.services.review_pipeline import maybe_enqueue_pipeline_for_revision
from app.workers.async_runner import run_worker_async
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


async def _maybe_enqueue_autostart_pipeline_for_revision(
    session,
    *,
    workspace_id: UUID,
    revision_id: UUID,
) -> UUID | None:
    return await maybe_enqueue_pipeline_for_revision(
        session,
        workspace_id=workspace_id,
        revision_id=revision_id,
        trigger=GitHubIndexJobTriggerSource.autostart,
    )


def _coalesce_autostart_task_id(*, workspace_id: str, revision_id: str) -> str:
    return f"coalesce-autostart-{workspace_id}-{revision_id}"


def _resolution_synchronize_task_id(*, revision_id: str) -> str:
    return f"resolution-synchronize-{revision_id}"


def _schedule_coalesced_autostart(
    *,
    revision_id: str,
    workspace_id: str,
    schedule_at: str,
) -> None:
    deadline = datetime.fromisoformat(schedule_at)
    remaining_seconds = max(0, int((deadline - datetime.now(UTC)).total_seconds()))
    schedule_autostart_pipeline_for_revision.apply_async(
        kwargs={
            "revision_id": revision_id,
            "workspace_id": workspace_id,
        },
        countdown=remaining_seconds,
        task_id=_coalesce_autostart_task_id(workspace_id=workspace_id, revision_id=revision_id),
    )


async def _head_revision_id_for_pull_request(
    session,
    *,
    pull_request_id: UUID,
) -> UUID | None:
    pull_request = await session.get(GitHubPullRequestORM, pull_request_id)
    if pull_request is None:
        return None
    return await session.scalar(
        select(GitHubPullRequestRevisionORM.id)
        .where(
            GitHubPullRequestRevisionORM.pull_request_id == pull_request_id,
            GitHubPullRequestRevisionORM.head_sha == pull_request.head_sha,
        )
        .order_by(GitHubPullRequestRevisionORM.revision_number.desc())
        .limit(1)
    )


async def _cleanup_pending_index_job_after_resolution_failure(index_job_id: UUID) -> None:
    async with get_db_context() as session:
        failed = await fail_pending_index_job_for_resolution_error(
            session,
            index_job_id=index_job_id,
        )
        if not failed:
            return
        await finalize_pipeline_github_check_for_index_job(
            session,
            index_job_id=index_job_id,
            summary="Resolution pairing failed",
        )


@celery_app.task(name="app.workers.github_tasks.schedule_autostart_pipeline_for_revision")
def schedule_autostart_pipeline_for_revision(revision_id: str, workspace_id: str) -> None:
    async def _run() -> None:
        revision_uuid = UUID(revision_id)
        job_id: UUID | None = None
        async with get_db_context() as session:
            if not await is_authoritative_for_pull_request_head(session, revision_id=revision_uuid):
                logger.info(
                    "autostart_coalesce_stale_revision",
                    extra={"revision_id": revision_id},
                )
                return
            job_id = await _maybe_enqueue_autostart_pipeline_for_revision(
                session,
                workspace_id=UUID(workspace_id),
                revision_id=revision_uuid,
            )
        if job_id is not None:
            enqueue_index_job(job_id)

    run_worker_async(_run())


def _handoff_stale_coalesce_resolution_task(
    *,
    stale_revision_id: str,
    coalesce_workspace_id: str,
    coalesce_schedule_at: str,
) -> None:
    async def _resolve_head_revision_id() -> str | None:
        async with get_db_context() as session:
            stale_revision = await session.get(
                GitHubPullRequestRevisionORM,
                UUID(stale_revision_id),
            )
            if stale_revision is None:
                return None
            head_revision_id = await _head_revision_id_for_pull_request(
                session,
                pull_request_id=stale_revision.pull_request_id,
            )
            if head_revision_id is None or head_revision_id == stale_revision.id:
                return None
            if not await is_authoritative_for_pull_request_head(
                session,
                revision_id=head_revision_id,
            ):
                return None
            return str(head_revision_id)

    head_revision_id = run_worker_async(_resolve_head_revision_id())
    if head_revision_id is None:
        return
    logger.info(
        "resolution_synchronize_coalesce_handoff",
        extra={
            "stale_revision_id": stale_revision_id,
            "head_revision_id": head_revision_id,
        },
    )
    apply_resolution_for_synchronize.apply_async(
        kwargs={
            "revision_id": head_revision_id,
            "index_job_id": None,
            "coalesce_workspace_id": coalesce_workspace_id,
            "coalesce_schedule_at": coalesce_schedule_at,
        },
        task_id=_resolution_synchronize_task_id(revision_id=head_revision_id),
    )


@celery_app.task(
    name="app.workers.github_tasks.apply_resolution_for_synchronize",
    bind=True,
    max_retries=3,
)
def apply_resolution_for_synchronize(
    self,
    revision_id: str,
    index_job_id: str | None = None,
    coalesce_workspace_id: str | None = None,
    coalesce_schedule_at: str | None = None,
    pair_resolution: bool = True,
) -> None:
    follow_up_index_job_id = UUID(index_job_id) if index_job_id is not None else None

    async def _run() -> str:
        revision_uuid = UUID(revision_id)
        async with get_db_context() as session:
            if not await is_authoritative_for_pull_request_head(session, revision_id=revision_uuid):
                logger.info(
                    "resolution_synchronize_stale_revision",
                    extra={"revision_id": revision_id},
                )
                return "skipped_stale"
            revision = await session.get(GitHubPullRequestRevisionORM, revision_uuid)
            if revision is None:
                logger.warning(
                    "resolution_synchronize_task_permanent_failure",
                    extra={"revision_id": revision_id, "error": "resolution_revision_not_found"},
                )
                return "skipped_permanent"
            pull_request = await session.get(GitHubPullRequestORM, revision.pull_request_id)
            if pull_request is None:
                logger.warning(
                    "resolution_synchronize_task_permanent_failure",
                    extra={
                        "revision_id": revision_id,
                        "error": "resolution_pull_request_not_found",
                    },
                )
                return "skipped_permanent"
            if pair_resolution:
                await apply_resolution_status_for_synchronize(
                    session,
                    pull_request=pull_request,
                    new_revision=revision,
                )
            await session.commit()
        return "applied"

    def _run_post_outcome(outcome: str) -> None:
        if outcome == "applied":
            if follow_up_index_job_id is not None:
                enqueue_index_job(follow_up_index_job_id)
            elif coalesce_workspace_id is not None and coalesce_schedule_at is not None:
                _schedule_coalesced_autostart(
                    revision_id=revision_id,
                    workspace_id=coalesce_workspace_id,
                    schedule_at=coalesce_schedule_at,
                )
        if (
            outcome == "skipped_stale"
            and coalesce_workspace_id is not None
            and coalesce_schedule_at is not None
        ):
            _handoff_stale_coalesce_resolution_task(
                stale_revision_id=revision_id,
                coalesce_workspace_id=coalesce_workspace_id,
                coalesce_schedule_at=coalesce_schedule_at,
            )
        if outcome in {"skipped_stale", "skipped_permanent"} and follow_up_index_job_id is not None:
            try:
                run_worker_async(
                    _cleanup_pending_index_job_after_resolution_failure(follow_up_index_job_id),
                )
            except Exception as cleanup_exc:  # noqa: BLE001
                logger.error(
                    "resolution_synchronize_cleanup_failed",
                    extra={
                        "revision_id": revision_id,
                        "index_job_id": str(follow_up_index_job_id),
                        "error": str(cleanup_exc),
                    },
                )
        if (
            outcome == "skipped_permanent"
            and coalesce_workspace_id is not None
            and coalesce_schedule_at is not None
        ):
            _schedule_coalesced_autostart(
                revision_id=revision_id,
                workspace_id=coalesce_workspace_id,
                schedule_at=coalesce_schedule_at,
            )
        elif outcome not in {"applied", "skipped_stale", "skipped_permanent"}:
            logger.info(
                "resolution_synchronize_task_skipped",
                extra={"revision_id": revision_id, "outcome": outcome},
            )

    fatal_exc: Exception | None = None
    outcome: str | None = None
    try:
        outcome = run_worker_async(_run())
    except Retry:
        raise
    except Exception as exc:
        logger.error(
            "resolution_synchronize_task_failed",
            extra={"revision_id": revision_id, "error": str(exc), "retries": self.request.retries},
        )
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=15 * (2**self.request.retries)) from exc
        fatal_exc = exc
    if fatal_exc is not None:
        if follow_up_index_job_id is not None:
            try:
                run_worker_async(
                    _cleanup_pending_index_job_after_resolution_failure(follow_up_index_job_id),
                )
            except Exception as cleanup_exc:  # noqa: BLE001
                logger.error(
                    "resolution_synchronize_cleanup_failed",
                    extra={
                        "revision_id": revision_id,
                        "index_job_id": str(follow_up_index_job_id),
                        "error": str(cleanup_exc),
                    },
                )
        if coalesce_workspace_id is not None and coalesce_schedule_at is not None:
            _schedule_coalesced_autostart(
                revision_id=revision_id,
                workspace_id=coalesce_workspace_id,
                schedule_at=coalesce_schedule_at,
            )
        raise fatal_exc

    post_outcome_exc: Exception | None = None
    try:
        assert outcome is not None
        _run_post_outcome(outcome)
    except Exception as exc:
        logger.error(
            "resolution_synchronize_post_outcome_failed",
            extra={"revision_id": revision_id, "error": str(exc), "retries": self.request.retries},
        )
        if self.request.retries < self.max_retries:
            raise self.retry(
                exc=exc,
                countdown=15 * (2**self.request.retries),
                kwargs={
                    "revision_id": revision_id,
                    "index_job_id": index_job_id,
                    "coalesce_workspace_id": coalesce_workspace_id,
                    "coalesce_schedule_at": coalesce_schedule_at,
                    "pair_resolution": False,
                },
            ) from exc
        post_outcome_exc = exc
    if post_outcome_exc is not None:
        if follow_up_index_job_id is not None:
            try:
                run_worker_async(
                    _cleanup_pending_index_job_after_resolution_failure(follow_up_index_job_id),
                )
            except Exception as cleanup_exc:  # noqa: BLE001
                logger.error(
                    "resolution_synchronize_cleanup_failed",
                    extra={
                        "revision_id": revision_id,
                        "index_job_id": str(follow_up_index_job_id),
                        "error": str(cleanup_exc),
                    },
                )
        if (
            coalesce_workspace_id is not None
            and coalesce_schedule_at is not None
            and outcome != "skipped_stale"
        ):
            _schedule_coalesced_autostart(
                revision_id=revision_id,
                workspace_id=coalesce_workspace_id,
                schedule_at=coalesce_schedule_at,
            )
        raise post_outcome_exc


@celery_app.task(name="app.workers.github_tasks.process_github_event", bind=True, max_retries=3)
def process_github_event(self, delivery_id: str) -> None:
    index_job_ids: list[UUID] = []
    resolution_follow_ups: list[tuple[str, UUID | None, str | None, str | None, bool]] = []

    async def _run() -> None:
        async with get_db_context() as session:
            delivery = await session.get(GitHubWebhookDeliveryORM, delivery_id)
            if delivery is None:
                raise RuntimeError("github_delivery_not_found")

            payload = delivery.payload_json
            event_type = delivery.event_type

            if event_type == "installation":
                installation = payload.get("installation")
                action = payload.get("action")
                if (
                    isinstance(installation, dict)
                    and isinstance(action, str)
                    and isinstance(installation.get("id"), int)
                ):
                    await apply_installation_webhook_event(
                        session,
                        github_installation_id=installation["id"],
                        action=action,
                    )

            elif event_type == "pull_request":
                result = await apply_pull_request_webhook_event(session, payload)
                if (
                    result is not None
                    and result.action in {"opened", "synchronize"}
                    and (result.new_revision or result.pipeline_retrigger)
                ):
                    if result.action == "synchronize":
                        paired_index_job_id: UUID | None = None
                        coalesce_workspace_id: str | None = None
                        coalesce_schedule_at: str | None = None
                        if settings.review_coalesce_seconds > 0:
                            coalesce_workspace_id = str(result.workspace_id)
                            coalesce_schedule_at = (
                                datetime.now(UTC)
                                + timedelta(seconds=settings.review_coalesce_seconds)
                            ).isoformat()
                        else:
                            paired_index_job_id = await _maybe_enqueue_autostart_pipeline_for_revision(
                                session,
                                workspace_id=result.workspace_id,
                                revision_id=result.revision_id,
                            )
                        resolution_follow_ups.append(
                            (
                                str(result.revision_id),
                                paired_index_job_id,
                                coalesce_workspace_id,
                                coalesce_schedule_at,
                                result.new_revision,
                            ),
                        )
                    else:
                        job_id = await _maybe_enqueue_autostart_pipeline_for_revision(
                            session,
                            workspace_id=result.workspace_id,
                            revision_id=result.revision_id,
                        )
                        if job_id is not None:
                            index_job_ids.append(job_id)

            elif event_type == "issue_comment":
                intent = await apply_issue_comment_webhook_event(session, payload)
                if intent is not None:
                    await supersede_active_generations_for_revision(
                        session,
                        revision_id=intent.revision_id,
                    )
                    job_id = await maybe_enqueue_pipeline_for_revision(
                        session,
                        workspace_id=intent.workspace_id,
                        revision_id=intent.revision_id,
                        trigger=GitHubIndexJobTriggerSource.command,
                    )
                    if job_id is not None:
                        index_job_ids.append(job_id)

            elif event_type == "pull_request_review":
                await apply_pull_request_review_webhook_event(session, payload)

            elif event_type == "installation_repositories":
                await apply_installation_repositories_webhook_event(session, payload)

            elif event_type == "push":
                logger.info(
                    "github_webhook_event_stub",
                    extra={
                        "delivery_id": delivery_id,
                        "event_type": event_type,
                        "installation_id": delivery.installation_id,
                    },
                )

            else:
                logger.info(
                    "github_webhook_event_unhandled",
                    extra={"delivery_id": delivery_id, "event_type": event_type},
                )

    try:
        run_worker_async(_run())
    except Exception as exc:
        logger.error(
            "github_webhook_task_failed",
            extra={"delivery_id": delivery_id, "error": str(exc), "retries": self.request.retries},
        )
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=15 * (2**self.request.retries)) from exc
        raise
    else:
        deferred_index_job_ids: set[UUID] = set()
        for (
            revision_id,
            follow_up_index_job_id,
            coalesce_workspace_id,
            coalesce_schedule_at,
            pair_resolution,
        ) in resolution_follow_ups:
            if follow_up_index_job_id is not None:
                deferred_index_job_ids.add(follow_up_index_job_id)
            apply_resolution_for_synchronize.delay(
                revision_id,
                index_job_id=(
                    str(follow_up_index_job_id) if follow_up_index_job_id is not None else None
                ),
                coalesce_workspace_id=coalesce_workspace_id,
                coalesce_schedule_at=coalesce_schedule_at,
                pair_resolution=pair_resolution,
            )
        for job_id in index_job_ids:
            if job_id not in deferred_index_job_ids:
                enqueue_index_job(job_id)
