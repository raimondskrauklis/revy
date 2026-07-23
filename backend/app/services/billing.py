# backend/app/services/billing.py
"""Billing helpers — docs/backend/BILLING.md."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ForbiddenError
from app.models.workspaces import WorkspaceORM

PLAN_LIMITS: dict[str, dict[str, int]] = {
    "free": {"seats": 3, "api_calls_per_day": 1_000},
    "pro": {"seats": 25, "api_calls_per_day": 50_000},
    "enterprise": {"seats": 10_000, "api_calls_per_day": 1_000_000},
}


async def get_workspace_plan(session: AsyncSession, workspace_id: UUID) -> str:
    workspace = await session.get(WorkspaceORM, workspace_id)
    if workspace is None:
        return "free"
    return workspace.plan or "free"


async def require_plan_feature(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    feature: str,
    minimum_plan: str = "pro",
) -> None:
    """Backend plan gating — never rely on frontend-only checks."""
    plan_order = ["free", "pro", "enterprise"]
    current = await get_workspace_plan(session, workspace_id)
    if plan_order.index(current) < plan_order.index(minimum_plan):
        raise ForbiddenError(
            message=f"Feature '{feature}' requires {minimum_plan} plan",
            error_code="forbidden",
            details={"feature": feature, "current_plan": current, "required_plan": minimum_plan},
        )


def plan_limit(plan: str, key: str) -> int:
    return PLAN_LIMITS.get(plan, PLAN_LIMITS["free"]).get(key, 0)
