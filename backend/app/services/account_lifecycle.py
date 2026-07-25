# backend/app/services/account_lifecycle.py
"""Account and workspace lifecycle — ACCOUNT_LIFECYCLE.md."""
from __future__ import annotations

from uuid import UUID

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import AppRole, PlatformRole, UserStatus, WorkspaceStatus
from app.core.exceptions import ForbiddenError, NotFoundError, ValidationError
from app.models.users import UserORM
from app.models.workspace_memberships import WorkspaceMembershipORM
from app.models.workspaces import WorkspaceORM
from app.services.audit_service import record_audit
from app.services.billing import effective_plan
from app.services.memberships import _assert_not_last_admin, _count_workspace_admins


async def leave_workspace(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    user_id: UUID,
    impersonator_user_id: UUID | None = None,
) -> None:
    membership = await session.scalar(
        select(WorkspaceMembershipORM)
        .where(
            WorkspaceMembershipORM.workspace_id == workspace_id,
            WorkspaceMembershipORM.user_id == user_id,
        )
        .with_for_update()
    )
    if membership is None:
        raise NotFoundError("Member not found")

    await _assert_not_last_admin(session, workspace_id=workspace_id, membership=membership)
    await session.delete(membership)
    await session.flush()

    await record_audit(
        session,
        actor_user_id=user_id,
        impersonator_user_id=impersonator_user_id,
        workspace_id=workspace_id,
        action="workspace.left",
        resource_type="workspace",
        resource_id=str(workspace_id),
    )


async def delete_workspace(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    confirm_slug: str,
    actor_user_id: UUID,
    impersonator_user_id: UUID | None = None,
) -> None:
    workspace = await session.scalar(
        select(WorkspaceORM).where(WorkspaceORM.id == workspace_id).with_for_update()
    )
    if workspace is None:
        raise NotFoundError("Workspace not found")
    if workspace.status == WorkspaceStatus.deleted:
        raise NotFoundError("Workspace not found")

    if workspace.slug != confirm_slug.strip():
        raise ValidationError(
            message="Workspace slug confirmation does not match",
            field="confirm_slug",
        )

    if effective_plan(workspace) == "pro" and workspace.stripe_customer_id:
        raise ForbiddenError(
            message="Cancel your subscription before deleting this workspace",
            error_code="subscription_active",
        )

    workspace.status = WorkspaceStatus.deleted
    await session.execute(
        delete(WorkspaceMembershipORM).where(WorkspaceMembershipORM.workspace_id == workspace_id)
    )
    await session.flush()

    await record_audit(
        session,
        actor_user_id=actor_user_id,
        impersonator_user_id=impersonator_user_id,
        workspace_id=workspace_id,
        action="workspace.deleted",
        resource_type="workspace",
        resource_id=str(workspace_id),
        metadata={"slug": workspace.slug},
    )


async def _assert_not_sole_workspace_admin(session: AsyncSession, *, user_id: UUID) -> None:
    admin_memberships = (
        await session.scalars(
            select(WorkspaceMembershipORM).where(
                WorkspaceMembershipORM.user_id == user_id,
                WorkspaceMembershipORM.role == AppRole.admin,
            )
        )
    ).all()

    checked_workspace_ids: set[UUID] = set()
    for membership in admin_memberships:
        workspace_id = membership.workspace_id
        if workspace_id in checked_workspace_ids:
            continue
        checked_workspace_ids.add(workspace_id)

        workspace = await session.scalar(
            select(WorkspaceORM).where(WorkspaceORM.id == workspace_id).with_for_update()
        )
        if workspace is None:
            raise NotFoundError("Workspace not found")

        admin_count = await _count_workspace_admins(session, workspace_id=workspace_id)
        if admin_count <= 1:
            raise ForbiddenError(
                message="You are the only admin of a workspace. Transfer admin role or delete the workspace first.",
                error_code="sole_workspace_admin",
            )


async def delete_account(
    session: AsyncSession,
    *,
    user_id: UUID,
    confirm_email: str,
    impersonator_user_id: UUID | None = None,
) -> None:
    user = await session.scalar(select(UserORM).where(UserORM.id == user_id).with_for_update())
    if user is None:
        raise NotFoundError("User not found")
    if user.status == UserStatus.deleted:
        raise NotFoundError("User not found")

    if user.email.lower() != confirm_email.strip().lower():
        raise ValidationError(
            message="Email confirmation does not match",
            field="confirm_email",
        )

    if user.platform_role == PlatformRole.super_admin:
        raise ForbiddenError(
            message="Platform administrators cannot delete their account via the app",
            error_code="platform_admin_protected",
        )

    await _assert_not_sole_workspace_admin(session, user_id=user_id)

    user.status = UserStatus.deleted
    user.email = f"deleted+{user.id}@revy.invalid"
    user.full_name = None
    await session.execute(delete(WorkspaceMembershipORM).where(WorkspaceMembershipORM.user_id == user_id))
    await session.flush()

    await record_audit(
        session,
        actor_user_id=user_id,
        impersonator_user_id=impersonator_user_id,
        workspace_id=None,
        action="user.deleted",
        resource_type="user",
        resource_id=str(user_id),
    )
