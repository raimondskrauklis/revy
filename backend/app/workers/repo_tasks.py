# backend/app/workers/repo_tasks.py
"""Repository sync Celery tasks — repo_sync queue."""
from __future__ import annotations

from uuid import UUID

import httpx

from app.core.database import get_db_context
from app.core.logging import get_logger
from app.integrations.github_api import list_installation_repositories
from app.models.github_installation import GitHubInstallationORM
from app.services.github_repositories import reconcile_repositories_from_api
from app.workers.async_runner import run_worker_async
from app.workers.celery_app import celery_app

logger = get_logger(__name__)


@celery_app.task(
    name="app.workers.repo_tasks.sync_installation_repositories",
    bind=True,
    max_retries=3,
)
def sync_installation_repositories(self, installation_id: str) -> None:
    async def _run() -> None:
        async with get_db_context() as session:
            installation = await session.get(GitHubInstallationORM, UUID(installation_id))
            if installation is None:
                raise RuntimeError("github_installation_not_found")

            async with httpx.AsyncClient(timeout=30.0) as client:
                repos = await list_installation_repositories(
                    client,
                    github_installation_id=installation.github_installation_id,
                )

            await reconcile_repositories_from_api(session, installation=installation, repos=repos)
            logger.info(
                "github_repository_sync_complete",
                extra={
                    "installation_id": installation_id,
                    "repo_count": len(repos),
                },
            )

    try:
        run_worker_async(_run())
    except Exception as exc:
        logger.error(
            "github_repository_sync_failed",
            extra={
                "installation_id": installation_id,
                "error": str(exc),
                "retries": self.request.retries,
            },
        )
        if self.request.retries < self.max_retries:
            raise self.retry(exc=exc, countdown=30 * (2**self.request.retries)) from exc
        raise
