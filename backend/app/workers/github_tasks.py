# backend/app/workers/github_tasks.py
"""GitHub webhook Celery tasks — github_events queue."""
from __future__ import annotations

from uuid import UUID

from celery.exceptions import Retry

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


@celery_app.task(
    name="app.workers.github_tasks.apply_resolution_for_synchronize",
    bind=True,
    max_retries=3,
)
def apply_resolution_for_synchronize(self, revision_id: str, index_job_id: str | None = None) -> None:
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
            await apply_resolution_status_for_synchronize(
                session,
                pull_request=pull_request,
                new_revision=revision,
            )
            await session.commit()
        return "applied"

    fatal_exc: Exception | None = None
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

            async def _fail_follow_up() -> None:
                async with get_db_context() as session:
                    await fail_pending_index_job_for_resolution_error(
                        session,
                        index_job_id=follow_up_index_job_id,
                    )

            run_worker_async(_fail_follow_up())
        raise fatal_exc
    if outcome == "applied" and follow_up_index_job_id is not None:
        enqueue_index_job(follow_up_index_job_id)
    elif outcome != "applied":
        logger.info(
            "resolution_synchronize_task_skipped",
            extra={"revision_id": revision_id, "outcome": outcome},
        )


@celery_app.task(name="app.workers.github_tasks.process_github_event", bind=True, max_retries=3)
def process_github_event(self, delivery_id: str) -> None:
    index_job_ids: list[UUID] = []
    resolution_follow_ups: list[tuple[str, UUID | None]] = []

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
                        if settings.review_coalesce_seconds > 0:
                            schedule_autostart_pipeline_for_revision.apply_async(
                                kwargs={
                                    "revision_id": str(result.revision_id),
                                    "workspace_id": str(result.workspace_id),
                                },
                                countdown=settings.review_coalesce_seconds,
                            )
                        else:
                            paired_index_job_id = await _maybe_enqueue_autostart_pipeline_for_revision(
                                session,
                                workspace_id=result.workspace_id,
                                revision_id=result.revision_id,
                            )
                            if paired_index_job_id is not None:
                                index_job_ids.append(paired_index_job_id)
                        resolution_follow_ups.append(
                            (str(result.revision_id), paired_index_job_id),
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
        for revision_id, follow_up_index_job_id in resolution_follow_ups:
            if follow_up_index_job_id is not None:
                deferred_index_job_ids.add(follow_up_index_job_id)
            apply_resolution_for_synchronize.delay(
                revision_id,
                index_job_id=(
                    str(follow_up_index_job_id) if follow_up_index_job_id is not None else None
                ),
            )
        for job_id in index_job_ids:
            if job_id not in deferred_index_job_ids:
                enqueue_index_job(job_id)
