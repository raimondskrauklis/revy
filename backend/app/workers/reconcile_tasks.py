# backend/app/workers/reconcile_tasks.py
"""Reconciliation Celery tasks — reconciliation queue."""
from __future__ import annotations

import time
from uuid import UUID

from sqlalchemy import select

from app.core.database import get_db_context
from app.core.logging import get_logger
from app.models.github_pull_request import GitHubPullRequestORM, GitHubPullRequestRevisionORM
from app.models.github_review_run import GitHubReviewRunORM
from app.services.github_finding_closure import (
    apply_pass2_closure_for_review_run,
    verify_still_open_escalation_groups,
)
from app.services.github_finding_judge import (
    JudgeCandidateArtifact,
    record_review_run_judge_status,
)
from app.services.github_finding_reconcile import reconcile_review_run
from app.services.github_generation_lifecycle import is_review_run_superseded
from app.services.github_pipeline_trace import (
    finalize_pipeline_github_check_for_review_run,
    get_pipeline_run_for_review_run,
    record_judge_pipeline_step,
    record_reconcile_pipeline_step,
)
from app.services.github_publish import enqueue_publish_for_review_run
from app.services.github_resolution_metrics import compute_resolution_transitions
from app.workers.async_runner import run_worker_async
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(
    name="app.workers.reconcile_tasks.reconcile_review_run",
    bind=True,
    max_retries=3,
    queue="reconciliation",
)
def reconcile_review_run_task(self, review_run_id: str) -> None:
    async def _run() -> None:
        async with get_db_context() as session:
            started = time.monotonic()
            group_ids = await reconcile_review_run(session, review_run_id=UUID(review_run_id))
            reconcile_ms = int((time.monotonic() - started) * 1000)

            pass2_started = time.monotonic()
            closed_count = await apply_pass2_closure_for_review_run(
                session,
                review_run_id=UUID(review_run_id),
            )
            pass2_ms = int((time.monotonic() - pass2_started) * 1000)

            judge_artifacts: list[JudgeCandidateArtifact] = []
            judge_started = time.monotonic()
            judged = await record_review_run_judge_status(
                session,
                review_run_id=UUID(review_run_id),
                artifacts_out=judge_artifacts,
            )
            judge_ms = int((time.monotonic() - judge_started) * 1000)

            verification_started = time.monotonic()
            verification_result = await verify_still_open_escalation_groups(
                session,
                review_run_id=UUID(review_run_id),
            )
            verification_ms = int((time.monotonic() - verification_started) * 1000)

            review_run = await session.get(GitHubReviewRunORM, UUID(review_run_id))
            resolution_pass: dict[str, object] | None = None
            if review_run is not None:
                current_revision = await session.get(
                    GitHubPullRequestRevisionORM,
                    review_run.revision_id,
                )
                if current_revision is not None:
                    prior_revision = await session.scalar(
                        select(GitHubPullRequestRevisionORM).where(
                            GitHubPullRequestRevisionORM.pull_request_id
                            == current_revision.pull_request_id,
                            GitHubPullRequestRevisionORM.revision_number
                            == current_revision.revision_number - 1,
                        )
                    )
                    if prior_revision is not None:
                        pull_request = await session.get(
                            GitHubPullRequestORM,
                            current_revision.pull_request_id,
                        )
                        if pull_request is not None:
                            await session.flush()
                            resolution_pass = await compute_resolution_transitions(
                                session,
                                pull_request=pull_request,
                                prior_revision=prior_revision,
                                current_revision=current_revision,
                            )

            pipeline_run = await get_pipeline_run_for_review_run(
                session,
                review_run_id=UUID(review_run_id),
            )
            if pipeline_run is not None:
                await record_reconcile_pipeline_step(
                    session,
                    pipeline_run_id=pipeline_run.id,
                    group_count=len(group_ids),
                    duration_ms=max(reconcile_ms + pass2_ms, 0),
                    resolution_pass=resolution_pass,
                )
                await record_judge_pipeline_step(
                    session,
                    pipeline_run_id=pipeline_run.id,
                    judged_count=judged,
                    duration_ms=max(judge_ms + verification_ms, 0),
                    candidates=judge_artifacts,
                    verification_judged_count=verification_result.judged_count,
                    verification_candidates=verification_result.artifacts,
                )

            if review_run is not None and is_review_run_superseded(review_run):
                logger.info(
                    "publish_enqueue_skipped_superseded",
                    extra={"review_run_id": review_run_id},
                )
                await session.commit()
                return

            await session.commit()
            enqueue_publish_for_review_run(UUID(review_run_id))
            logger.info(
                "github_reconcile_complete",
                extra={
                    "review_run_id": review_run_id,
                    "group_count": len(group_ids),
                    "pass2_closed_count": closed_count,
                    "judge_outcomes": judged,
                    "verification_outcomes": verification_result.judged_count,
                    "reconcile_ms": reconcile_ms,
                    "pass2_ms": pass2_ms,
                },
            )

    try:
        run_worker_async(_run())
    except Exception as exc:
        logger.error(
            "github_reconcile_task_failed",
            extra={
                "review_run_id": review_run_id,
                "error": str(exc),
                "retries": self.request.retries,
            },
        )
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=60 * (2**self.request.retries)) from exc

        error_message = str(exc)

        async def _finalize() -> None:
            async with get_db_context() as session:
                await finalize_pipeline_github_check_for_review_run(
                    session,
                    review_run_id=UUID(review_run_id),
                    summary=error_message,
                )
                await session.commit()

        run_worker_async(_finalize())
        raise
