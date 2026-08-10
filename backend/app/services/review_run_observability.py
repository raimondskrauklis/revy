# backend/app/services/review_run_observability.py
"""Review run observability checkpoint + permanent failure — pipeline observability."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import GitHubReviewRunStatus
from app.core.database import get_db_context
from app.models.github_review_run import GitHubReviewRunORM
from app.services.observability_failure import classify_failure_class


def build_partial_timing_stats(
    *,
    retrieve_duration_ms: int,
    compare_ms: int = 0,
    supplemental_ms: int = 0,
) -> dict[str, int | str]:
    return {
        "stats_version": 1,
        "retrieve_ms": retrieve_duration_ms,
        "compare_ms": compare_ms,
        "supplemental_ms": supplemental_ms,
    }


async def commit_review_run_observability_checkpoint(
    session: AsyncSession,
    run: GitHubReviewRunORM,
    *,
    retrieve_duration_ms: int,
    compare_ms: int = 0,
    supplemental_ms: int = 0,
) -> None:
    run.failure_stage = "retrieve"
    run.timing_stats = build_partial_timing_stats(
        retrieve_duration_ms=retrieve_duration_ms,
        compare_ms=compare_ms,
        supplemental_ms=supplemental_ms,
    )
    await session.commit()
    await session.refresh(run)


async def persist_review_run_permanent_failure(
    *,
    review_run_id: UUID,
    error_message: str,
    failure_stage: str | None = None,
    exc: BaseException | None = None,
) -> None:
    failure_class = classify_failure_class(exc) if exc is not None else None
    async with get_db_context() as session:
        run = await session.get(GitHubReviewRunORM, review_run_id)
        if run is None:
            return
        if run.status in (GitHubReviewRunStatus.completed, GitHubReviewRunStatus.failed):
            return
        run.status = GitHubReviewRunStatus.failed
        run.error_message = error_message[:2000]
        if failure_stage is not None:
            run.failure_stage = failure_stage
        if failure_class is not None:
            run.failure_class = failure_class
        await session.commit()
