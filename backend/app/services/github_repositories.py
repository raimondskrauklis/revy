# backend/app/services/github_repositories.py
"""GitHub repository metadata — R1 repository sync."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import GitHubRepositoryStatus
from app.core.exceptions import NotFoundError, ValidationError
from app.core.logging import get_logger
from app.core.pagination import (
    CursorMeta,
    CursorParams,
    CursorResponse,
    InvalidCursorError,
    decode_cursor,
    encode_cursor,
)
from app.models.github_installation import GitHubInstallationORM
from app.models.github_repository import GitHubRepositoryORM
from app.schemas.github_repository import GitHubRepositoryResponse

logger = get_logger(__name__)


def _repo_fields_from_github(repo: dict[str, Any]) -> dict[str, Any] | None:
    raw_id = repo.get("id")
    name = repo.get("name")
    full_name = repo.get("full_name")
    if not isinstance(raw_id, int) or not isinstance(name, str) or not isinstance(full_name, str):
        return None

    default_branch = repo.get("default_branch")
    html_url = repo.get("html_url")
    return {
        "github_repository_id": raw_id,
        "name": name,
        "full_name": full_name,
        "default_branch": default_branch if isinstance(default_branch, str) else None,
        "private": bool(repo.get("private")),
        "html_url": html_url if isinstance(html_url, str) else None,
    }


async def _get_installation_for_workspace(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    installation_id: UUID,
) -> GitHubInstallationORM:
    row = await session.scalar(
        select(GitHubInstallationORM).where(
            GitHubInstallationORM.id == installation_id,
            GitHubInstallationORM.workspace_id == workspace_id,
        )
    )
    if row is None:
        raise NotFoundError("GitHub installation not found")
    return row


async def _find_repository(
    session: AsyncSession,
    *,
    installation_id: UUID,
    github_repository_id: int,
) -> GitHubRepositoryORM | None:
    return await session.scalar(
        select(GitHubRepositoryORM).where(
            GitHubRepositoryORM.installation_id == installation_id,
            GitHubRepositoryORM.github_repository_id == github_repository_id,
        )
    )


async def upsert_repository_from_github(
    session: AsyncSession,
    *,
    installation: GitHubInstallationORM,
    repo: dict[str, Any],
) -> GitHubRepositoryORM | None:
    fields = _repo_fields_from_github(repo)
    if fields is None:
        return None

    existing = await _find_repository(
        session,
        installation_id=installation.id,
        github_repository_id=fields["github_repository_id"],
    )
    if existing is None:
        row = GitHubRepositoryORM(
            installation_id=installation.id,
            workspace_id=installation.workspace_id,
            status=GitHubRepositoryStatus.active,
            **fields,
        )
        session.add(row)
        await session.flush()
        return row

    existing.name = fields["name"]
    existing.full_name = fields["full_name"]
    existing.default_branch = fields["default_branch"]
    existing.private = fields["private"]
    existing.html_url = fields["html_url"]
    existing.status = GitHubRepositoryStatus.active
    await session.flush()
    return existing


async def mark_repository_removed(
    session: AsyncSession,
    *,
    installation: GitHubInstallationORM,
    repo: dict[str, Any],
) -> GitHubRepositoryORM | None:
    fields = _repo_fields_from_github(repo)
    if fields is None:
        return None

    existing = await _find_repository(
        session,
        installation_id=installation.id,
        github_repository_id=fields["github_repository_id"],
    )
    if existing is None:
        return None

    existing.status = GitHubRepositoryStatus.removed
    await session.flush()
    return existing


async def apply_installation_repositories_webhook_event(
    session: AsyncSession,
    payload: dict[str, Any],
) -> None:
    installation_payload = payload.get("installation")
    if not isinstance(installation_payload, dict):
        return

    raw_installation_id = installation_payload.get("id")
    if not isinstance(raw_installation_id, int):
        return

    installation = await session.scalar(
        select(GitHubInstallationORM).where(
            GitHubInstallationORM.github_installation_id == raw_installation_id,
        )
    )
    if installation is None:
        logger.warning(
            "github_repository_orphan_installation",
            extra={"github_installation_id": raw_installation_id},
        )
        return

    added = payload.get("repositories_added")
    if isinstance(added, list):
        for repo in added:
            if isinstance(repo, dict):
                await upsert_repository_from_github(session, installation=installation, repo=repo)

    removed = payload.get("repositories_removed")
    if isinstance(removed, list):
        for repo in removed:
            if isinstance(repo, dict):
                await mark_repository_removed(session, installation=installation, repo=repo)


async def reconcile_repositories_from_api(
    session: AsyncSession,
    *,
    installation: GitHubInstallationORM,
    repos: list[dict[str, Any]],
) -> None:
    seen_ids: set[int] = set()
    for repo in repos:
        row = await upsert_repository_from_github(session, installation=installation, repo=repo)
        if row is not None:
            seen_ids.add(row.github_repository_id)

    active_rows = list(
        await session.scalars(
            select(GitHubRepositoryORM).where(
                GitHubRepositoryORM.installation_id == installation.id,
                GitHubRepositoryORM.status == GitHubRepositoryStatus.active,
            )
        )
    )
    for row in active_rows:
        if row.github_repository_id not in seen_ids:
            row.status = GitHubRepositoryStatus.removed
    await session.flush()


async def list_github_repositories(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    installation_id: UUID,
    params: CursorParams,
    include_removed: bool = False,
) -> CursorResponse[GitHubRepositoryResponse]:
    await _get_installation_for_workspace(
        session,
        workspace_id=workspace_id,
        installation_id=installation_id,
    )

    stmt = select(GitHubRepositoryORM).where(
        GitHubRepositoryORM.workspace_id == workspace_id,
        GitHubRepositoryORM.installation_id == installation_id,
    )
    if not include_removed:
        stmt = stmt.where(GitHubRepositoryORM.status == GitHubRepositoryStatus.active)

    if params.cursor:
        try:
            cursor_ts, cursor_id = decode_cursor(params.cursor)
        except InvalidCursorError as exc:
            raise ValidationError(message="Invalid cursor", field="cursor") from exc
        stmt = stmt.where(
            (GitHubRepositoryORM.created_at < cursor_ts)
            | ((GitHubRepositoryORM.created_at == cursor_ts) & (GitHubRepositoryORM.id < cursor_id))
        )

    stmt = stmt.order_by(
        GitHubRepositoryORM.created_at.desc(),
        GitHubRepositoryORM.id.desc(),
    ).limit(params.limit + 1)
    rows = list(await session.scalars(stmt))

    has_next = len(rows) > params.limit
    if has_next:
        rows = rows[: params.limit]

    next_cursor = None
    if has_next and rows:
        last = rows[-1]
        next_cursor = encode_cursor(last.created_at, last.id)

    return CursorResponse(
        items=[GitHubRepositoryResponse.model_validate(row) for row in rows],
        cursor=CursorMeta(next_cursor=next_cursor, has_next=has_next),
    )


def enqueue_installation_repository_sync(installation_id: UUID) -> None:
    from app.workers.repo_tasks import sync_installation_repositories

    sync_installation_repositories.delay(str(installation_id))
