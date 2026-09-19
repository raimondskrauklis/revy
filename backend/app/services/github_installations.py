# backend/app/services/github_installations.py
"""GitHub installations — REVY_PRODUCT_SLICE.md."""
from __future__ import annotations

from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import httpx
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import GitHubAccountType, GitHubInstallationStatus
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.core.pagination import (
    CursorMeta,
    CursorParams,
    CursorResponse,
    InvalidCursorError,
    decode_cursor,
    encode_cursor,
)
from app.core.plan_gates import workspace_has_feature
from app.integrations.github_api import list_installation_repositories
from app.models.github_installation import GitHubInstallationORM
from app.models.workspaces import WorkspaceORM
from app.schemas.github_installation import GitHubInstallationCreate, GitHubInstallationResponse


def _installation_conflict(
    existing: GitHubInstallationORM,
    *,
    workspace_id: UUID,
) -> ConflictError:
    if existing.workspace_id == workspace_id:
        return ConflictError(message="GitHub installation already registered for this workspace")
    return ConflictError(message="GitHub installation is linked to another workspace")


async def _find_installation_by_github_id(
    session: AsyncSession,
    github_installation_id: int,
) -> GitHubInstallationORM | None:
    return await session.scalar(
        select(GitHubInstallationORM).where(
            GitHubInstallationORM.github_installation_id == github_installation_id,
        )
    )


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
    workspace = await session.scalar(
        select(WorkspaceORM).where(WorkspaceORM.id == workspace_id).with_for_update()
    )
    if workspace is None:
        raise NotFoundError("Workspace not found")

    existing = await _find_installation_by_github_id(session, payload.github_installation_id)
    if existing is not None:
        raise _installation_conflict(existing, workspace_id=workspace_id)

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
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raced = await _find_installation_by_github_id(session, payload.github_installation_id)
        if raced is not None:
            raise _installation_conflict(raced, workspace_id=workspace_id) from exc
        raise ConflictError(message="GitHub installation already registered") from exc
    return installation


async def bind_github_installation(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    github_installation_id: int,
    account_login: str,
    account_type: GitHubAccountType,
    account_id: int,
    permissions_snapshot: dict[str, Any] | None = None,
) -> GitHubInstallationORM:
    workspace = await session.scalar(
        select(WorkspaceORM).where(WorkspaceORM.id == workspace_id).with_for_update()
    )
    if workspace is None:
        raise NotFoundError("Workspace not found")
    if not workspace_has_feature(workspace, "installations.create"):
        raise ForbiddenError(
            message="Plan upgrade required",
            error_code="plan_upgrade_required",
            details={"feature": "installations.create", "required_plan": "pro"},
        )

    existing = await _find_installation_by_github_id(session, github_installation_id)
    if existing is not None:
        if existing.workspace_id != workspace_id:
            raise _installation_conflict(existing, workspace_id=workspace_id)
        existing.account_login = account_login.strip()
        existing.account_type = account_type
        existing.account_id = account_id
        if permissions_snapshot is not None:
            existing.permissions_snapshot = permissions_snapshot
        existing.status = GitHubInstallationStatus.active
        await session.flush()
        return existing

    installation = GitHubInstallationORM(
        workspace_id=workspace_id,
        github_installation_id=github_installation_id,
        account_login=account_login.strip(),
        account_type=account_type,
        account_id=account_id,
        status=GitHubInstallationStatus.active,
        permissions_snapshot=permissions_snapshot,
        verified_at=None,
    )
    session.add(installation)
    try:
        await session.flush()
    except IntegrityError as exc:
        await session.rollback()
        raced = await _find_installation_by_github_id(session, github_installation_id)
        if raced is not None:
            if raced.workspace_id == workspace_id:
                return raced
            raise _installation_conflict(raced, workspace_id=workspace_id) from exc
        raise ConflictError(message="GitHub installation already registered") from exc
    return installation


async def verify_granted_repositories(
    session: AsyncSession,
    *,
    installation: GitHubInstallationORM,
    client: httpx.AsyncClient,
) -> GitHubInstallationORM:
    repos = await list_installation_repositories(
        client,
        github_installation_id=installation.github_installation_id,
    )
    if repos:
        installation.verified_at = datetime.now(UTC)
    else:
        installation.verified_at = None
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


_INSTALLATION_ACTION_STATUS: dict[str, GitHubInstallationStatus] = {
    "deleted": GitHubInstallationStatus.removed,
    "suspend": GitHubInstallationStatus.suspended,
    "unsuspend": GitHubInstallationStatus.active,
    "created": GitHubInstallationStatus.active,
    "new_permissions_accepted": GitHubInstallationStatus.active,
}


async def apply_installation_webhook_event(
    session: AsyncSession,
    *,
    github_installation_id: int,
    action: str,
) -> None:
    from app.core.logging import get_logger

    logger = get_logger(__name__)
    installation = await _find_installation_by_github_id(session, github_installation_id)
    if installation is None:
        logger.warning(
            "github_installation_orphan",
            extra={"github_installation_id": github_installation_id, "action": action},
        )
        return

    new_status = _INSTALLATION_ACTION_STATUS.get(action)
    if new_status is None:
        logger.info(
            "github_installation_action_ignored",
            extra={"github_installation_id": github_installation_id, "action": action},
        )
        return

    installation.status = new_status
    await session.flush()
