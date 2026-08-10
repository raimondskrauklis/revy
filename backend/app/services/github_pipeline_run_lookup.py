# backend/app/services/github_pipeline_run_lookup.py
"""Pipeline run lookups by foreign keys — isolated to avoid import cycles."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.github_pipeline import GitHubPipelineRunORM


async def get_pipeline_run_for_index_job(
    session: AsyncSession,
    *,
    index_job_id: UUID,
) -> GitHubPipelineRunORM | None:
    return await session.scalar(
        select(GitHubPipelineRunORM).where(GitHubPipelineRunORM.index_job_id == index_job_id)
    )


async def get_pipeline_runs_for_index_jobs(
    session: AsyncSession,
    *,
    index_job_ids: list[UUID],
) -> dict[UUID, GitHubPipelineRunORM]:
    if not index_job_ids:
        return {}
    rows = await session.scalars(
        select(GitHubPipelineRunORM).where(GitHubPipelineRunORM.index_job_id.in_(index_job_ids))
    )
    return {
        pipeline_run.index_job_id: pipeline_run
        for pipeline_run in rows
        if pipeline_run.index_job_id is not None
    }
