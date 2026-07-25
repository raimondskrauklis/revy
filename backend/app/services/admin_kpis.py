# backend/app/services/admin_kpis.py
"""Platform admin KPI aggregates — W5."""
from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import UserStatus, WorkspaceStatus
from app.models.users import UserORM
from app.models.workspaces import WorkspaceORM
from app.schemas.admin import AdminKpisResponse


async def get_admin_kpis(session: AsyncSession) -> AdminKpisResponse:
    workspaces_active = await session.scalar(
        select(func.count())
        .select_from(WorkspaceORM)
        .where(WorkspaceORM.status == WorkspaceStatus.active)
    )
    workspaces_suspended = await session.scalar(
        select(func.count())
        .select_from(WorkspaceORM)
        .where(WorkspaceORM.status == WorkspaceStatus.suspended)
    )
    workspaces_deleted = await session.scalar(
        select(func.count())
        .select_from(WorkspaceORM)
        .where(WorkspaceORM.status == WorkspaceStatus.deleted)
    )
    workspaces_total = int(workspaces_active or 0) + int(workspaces_suspended or 0)
    users_active = await session.scalar(
        select(func.count()).select_from(UserORM).where(UserORM.status == UserStatus.active)
    )
    users_pending_approval = await session.scalar(
        select(func.count())
        .select_from(UserORM)
        .where(UserORM.status == UserStatus.pending_approval)
    )

    return AdminKpisResponse(
        workspaces_total=workspaces_total,
        workspaces_active=int(workspaces_active or 0),
        workspaces_suspended=int(workspaces_suspended or 0),
        workspaces_deleted=int(workspaces_deleted or 0),
        users_active=int(users_active or 0),
        users_pending_approval=int(users_pending_approval or 0),
    )
