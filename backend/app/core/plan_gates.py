# backend/app/core/plan_gates.py
"""Workspace plan feature gating — boolean features only in v1.

Gated features (extend PLAN_FEATURES when adding pro-only APIs):
- installations.create → requires pro plan
"""
from __future__ import annotations

from typing import Annotated
from uuid import UUID

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.workspaces import WorkspaceORM
from app.services.billing import effective_plan

PLAN_FEATURES: dict[str, str] = {
    "installations.create": "pro",
}

PLAN_RANK: dict[str, int] = {
    "free": 0,
    "pro": 1,
}


def plan_meets_requirement(current_plan: str, required_plan: str) -> bool:
    return PLAN_RANK.get(current_plan, 0) >= PLAN_RANK.get(required_plan, 0)


def workspace_has_feature(workspace: WorkspaceORM, feature: str) -> bool:
    required_plan = PLAN_FEATURES.get(feature)
    if required_plan is None:
        return True
    return plan_meets_requirement(effective_plan(workspace), required_plan)


def require_plan_feature(feature: str):
    async def _dependency(
        workspace_id: UUID,
        session: Annotated[AsyncSession, Depends(get_db)],
    ) -> None:
        workspace = await session.get(WorkspaceORM, workspace_id)
        if workspace is None:
            raise NotFoundError("Workspace not found")
        if workspace_has_feature(workspace, feature):
            return
        required_plan = PLAN_FEATURES.get(feature, "pro")
        raise ForbiddenError(
            message="Plan upgrade required",
            error_code="plan_upgrade_required",
            details={"feature": feature, "required_plan": required_plan},
        )

    return _dependency
