# backend/app/workers/reconcile_tasks.py
"""Reconciliation Celery tasks — reconciliation queue."""
from __future__ import annotations

import asyncio
from uuid import UUID

from app.core.database import get_db_context
from app.core.logging import get_logger
from app.services.github_finding_judge import run_judge_for_review_run
from app.services.github_finding_reconcile import reconcile_review_run
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
            group_ids = await reconcile_review_run(session, review_run_id=UUID(review_run_id))
            judged = await run_judge_for_review_run(session, review_run_id=UUID(review_run_id))
            await session.commit()
            # Judge runs inline here; judge_review_run task is reserved for future fan-out.
            logger.info(
                "github_reconcile_complete",
                extra={
                    "review_run_id": review_run_id,
                    "group_count": len(group_ids),
                    "judge_outcomes": judged,
                },
            )

    try:
        asyncio.run(_run())
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
        raise
