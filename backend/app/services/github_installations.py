# backend/app/services/github_installations.py
"""GitHub installations — REVY_PRODUCT_SLICE.md."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import GitHubInstallationStatus
from app.core.exceptions import ConflictError, NotFoundError, ValidationError
from app.core.pagination import (
    CursorMeta,
    CursorParams,
    CursorResponse,
    InvalidCursorError,
    decode_cursor,
    encode_cursor,
)
from app.models.github_installation import GitHubInstallationORM
from app.schemas.github_installation import GitHubInstallationCreate, GitHubInstallationResponse


async def list_github_installations(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    params: CursorParams,
) -> CursorResponse[GitHubInstallationResponse]:
    stmt = select(GitHubInstallationORM).where(GitHubInstallationORM.workspace_id == workspace_id)

    if params.cursor:
        try:
            cursor_ts, cursor_id = decode_cursor(params.cursor)
        except InvalidCursorError as exc:
            raise ValidationError(message="Invalid cursor", field="cursor") from exc
        stmt = stmt.where(
            (GitHubInstallationORM.created_at < cursor_ts)
            | ((GitHubInstallationORM.created_at == cursor_ts) & (GitHubInstallationORM.id < cursor_id))
        )

    stmt = stmt.order_by(
        GitHubInstallationORM.created_at.desc(),
        GitHubInstallationORM.id.desc(),
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
        items=[GitHubInstallationResponse.model_validate(row) for row in rows],
        cursor=CursorMeta(next_cursor=next_cursor, has_next=has_next),
    )


async def create_github_installation(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    payload: GitHubInstallationCreate,
) -> GitHubInstallationORM:
    existing = await session.scalar(
        select(GitHubInstallationORM).where(
            GitHubInstallationORM.github_installation_id == payload.github_installation_id,
        )
    )
    if existing is not None:
        if existing.workspace_id == workspace_id:
            raise ConflictError(message="GitHub installation already registered for this workspace")
        raise ConflictError(message="GitHub installation is linked to another workspace")

    installation = GitHubInstallationORM(
        workspace_id=workspace_id,
        github_installation_id=payload.github_installation_id,
        account_login=payload.account_login.strip(),
        account_type=payload.account_type,
        account_id=payload.account_id,
        status=GitHubInstallationStatus.active,
        permissions_snapshot=payload.permissions_snapshot,
    )
    session.add(installation)
    await session.flush()
    return installation


async def get_github_installation(
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
