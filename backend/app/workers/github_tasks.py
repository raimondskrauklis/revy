# backend/app/workers/github_tasks.py
"""GitHub webhook Celery tasks — github_events queue."""
from __future__ import annotations

from uuid import UUID

from app.constants.enums import GitHubIndexJobTriggerSource
from app.core.config import settings
from app.core.database import get_db_context
from app.core.logging import get_logger
from app.models.github_webhook_delivery import GitHubWebhookDeliveryORM
from app.services.github_generation_lifecycle import (
    is_authoritative_for_pull_request_head,
    supersede_active_generations_for_revision,
)
from app.services.github_indexing import enqueue_index_job
from app.services.github_installations import apply_installation_webhook_event
from app.services.github_pull_requests import (
    apply_issue_comment_webhook_event,
    apply_pull_request_review_webhook_event,
    apply_pull_request_webhook_event,
)
from app.services.github_repositories import apply_installation_repositories_webhook_event
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


@celery_app.task(name="app.workers.github_tasks.process_github_event", bind=True, max_retries=3)
def process_github_event(self, delivery_id: str) -> None:
    index_job_ids: list[UUID] = []

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
                return

            if event_type == "pull_request":
                result = await apply_pull_request_webhook_event(session, payload)
                if (
                    result is not None
                    and result.action in {"opened", "synchronize"}
                    and (result.new_revision or result.pipeline_retrigger)
                ):
                    if (
                        result.action == "synchronize"
                        and settings.review_coalesce_seconds > 0
                    ):
                        schedule_autostart_pipeline_for_revision.apply_async(
                            kwargs={
                                "revision_id": str(result.revision_id),
                                "workspace_id": str(result.workspace_id),
                            },
                            countdown=settings.review_coalesce_seconds,
                        )
                    else:
                        job_id = await _maybe_enqueue_autostart_pipeline_for_revision(
                            session,
                            workspace_id=result.workspace_id,
                            revision_id=result.revision_id,
                        )
                        if job_id is not None:
                            index_job_ids.append(job_id)
                return

            if event_type == "issue_comment":
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
                return

            if event_type == "pull_request_review":
                await apply_pull_request_review_webhook_event(session, payload)
                return

            if event_type in {"push", "installation_repositories"}:
                if event_type == "installation_repositories":
                    await apply_installation_repositories_webhook_event(session, payload)
                    return

                logger.info(
                    "github_webhook_event_stub",
                    extra={
                        "delivery_id": delivery_id,
                        "event_type": event_type,
                        "installation_id": delivery.installation_id,
                    },
                )
                return

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
        for job_id in index_job_ids:
            enqueue_index_job(job_id)
