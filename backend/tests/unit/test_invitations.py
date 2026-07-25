# backend/tests/unit/test_invitations.py
"""Workspace invitation service — INVITATIONS.md."""
import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.constants.enums import AppRole, InvitationStatus, UserStatus
from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError, ValidationError
from app.models.invitations import WorkspaceInvitationORM
from app.models.users import UserORM
from app.models.workspace_memberships import WorkspaceMembershipORM
from app.services.invitations import (
    accept_invitation,
    create_invitation,
    list_invitations,
    revoke_invitation,
)


@pytest.mark.asyncio
async def test_create_invitation_persists_row():
    workspace_id = uuid.uuid4()
    inviter_id = uuid.uuid4()
    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[None, MagicMock(), None])
    session.add = MagicMock()
    session.flush = AsyncMock()

    invitation = await create_invitation(
        session,
        workspace_id=workspace_id,
        email="Colleague@Example.com",
        role=AppRole.viewer,
        invited_by_user_id=inviter_id,
    )

    session.add.assert_called()
    assert invitation.email == "colleague@example.com"
    assert invitation.role == AppRole.viewer
    assert invitation.status == InvitationStatus.pending
    assert invitation.workspace_id == workspace_id
    assert invitation.invited_by_user_id == inviter_id
    assert invitation.token


@pytest.mark.asyncio
async def test_create_invitation_rejects_invalid_email():
    session = AsyncMock()
    with pytest.raises(ValidationError):
        await create_invitation(
            session,
            workspace_id=uuid.uuid4(),
            email="not-an-email",
            role=AppRole.viewer,
            invited_by_user_id=uuid.uuid4(),
        )


@pytest.mark.asyncio
async def test_create_invitation_rejects_existing_member():
    workspace_id = uuid.uuid4()
    user = UserORM(
        keycloak_user_id="kc-member",
        email="member@example.com",
        status=UserStatus.active,
    )
    user.id = uuid.uuid4()
    membership = WorkspaceMembershipORM(
        user_id=user.id,
        workspace_id=workspace_id,
        role=AppRole.viewer,
    )

    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[user, membership])

    with pytest.raises(ConflictError, match="already a workspace member"):
        await create_invitation(
            session,
            workspace_id=workspace_id,
            email="member@example.com",
            role=AppRole.viewer,
            invited_by_user_id=uuid.uuid4(),
        )


@pytest.mark.asyncio
async def test_create_invitation_rejects_duplicate_pending():
    workspace_id = uuid.uuid4()
    pending = WorkspaceInvitationORM(
        workspace_id=workspace_id,
        email="pending@example.com",
        role=AppRole.viewer,
        token="existing-token",
        invited_by_user_id=uuid.uuid4(),
        status=InvitationStatus.pending,
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )

    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[None, MagicMock(), pending])

    with pytest.raises(ConflictError, match="pending invitation"):
        await create_invitation(
            session,
            workspace_id=workspace_id,
            email="pending@example.com",
            role=AppRole.viewer,
            invited_by_user_id=uuid.uuid4(),
        )


@pytest.mark.asyncio
async def test_accept_invitation_creates_membership():
    workspace_id = uuid.uuid4()
    user = UserORM(
        keycloak_user_id="kc-invitee",
        email="invitee@example.com",
        status=UserStatus.active,
    )
    user.id = uuid.uuid4()

    invitation = WorkspaceInvitationORM(
        workspace_id=workspace_id,
        email="invitee@example.com",
        role=AppRole.operator,
        token="accept-me",
        invited_by_user_id=uuid.uuid4(),
        status=InvitationStatus.pending,
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )

    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[invitation, None])
    session.add = MagicMock()
    session.flush = AsyncMock()

    membership = await accept_invitation(session, token="accept-me", user=user)

    assert membership.user_id == user.id
    assert membership.workspace_id == workspace_id
    assert membership.role == AppRole.operator
    assert invitation.status == InvitationStatus.accepted
    assert invitation.accepted_at is not None
    assert user.status == UserStatus.active


@pytest.mark.asyncio
async def test_accept_invitation_leaves_active_user_unchanged():
    workspace_id = uuid.uuid4()
    user = UserORM(
        keycloak_user_id="kc-active",
        email="active@example.com",
        status=UserStatus.active,
    )
    user.id = uuid.uuid4()

    invitation = WorkspaceInvitationORM(
        workspace_id=workspace_id,
        email="active@example.com",
        role=AppRole.viewer,
        token="active-token",
        invited_by_user_id=uuid.uuid4(),
        status=InvitationStatus.pending,
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )

    session = AsyncMock()
    session.scalar = AsyncMock(side_effect=[invitation, None])
    session.add = MagicMock()
    session.flush = AsyncMock()

    await accept_invitation(session, token="active-token", user=user)

    assert user.status == UserStatus.active


@pytest.mark.asyncio
async def test_accept_invitation_rejects_pending_profile():
    user = UserORM(
        keycloak_user_id="kc-profile",
        email="profile@example.com",
        status=UserStatus.pending_profile,
    )
    invitation = WorkspaceInvitationORM(
        workspace_id=uuid.uuid4(),
        email="profile@example.com",
        role=AppRole.viewer,
        token="token",
        invited_by_user_id=uuid.uuid4(),
        status=InvitationStatus.pending,
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=invitation)

    with pytest.raises(ForbiddenError, match="cannot accept invitations"):
        await accept_invitation(session, token="token", user=user)


@pytest.mark.asyncio
async def test_accept_invitation_rejects_pending_approval():
    user = UserORM(
        keycloak_user_id="kc-wait",
        email="wait@example.com",
        status=UserStatus.pending_approval,
    )
    invitation = WorkspaceInvitationORM(
        workspace_id=uuid.uuid4(),
        email="wait@example.com",
        role=AppRole.viewer,
        token="token",
        invited_by_user_id=uuid.uuid4(),
        status=InvitationStatus.pending,
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=invitation)

    with pytest.raises(ForbiddenError, match="cannot accept invitations"):
        await accept_invitation(session, token="token", user=user)


@pytest.mark.asyncio
async def test_accept_invitation_rejects_wrong_email():
    user = UserORM(
        keycloak_user_id="kc-other",
        email="other@example.com",
        status=UserStatus.active,
    )
    invitation = WorkspaceInvitationORM(
        workspace_id=uuid.uuid4(),
        email="invitee@example.com",
        role=AppRole.viewer,
        token="token",
        invited_by_user_id=uuid.uuid4(),
        status=InvitationStatus.pending,
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=invitation)

    with pytest.raises(ForbiddenError):
        await accept_invitation(session, token="token", user=user)


@pytest.mark.asyncio
async def test_accept_invitation_rejects_expired():
    user = UserORM(
        keycloak_user_id="kc-exp",
        email="invitee@example.com",
        status=UserStatus.active,
    )
    invitation = WorkspaceInvitationORM(
        workspace_id=uuid.uuid4(),
        email="invitee@example.com",
        role=AppRole.viewer,
        token="expired",
        invited_by_user_id=uuid.uuid4(),
        status=InvitationStatus.pending,
        expires_at=datetime.now(UTC) - timedelta(hours=1),
    )

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=invitation)

    with pytest.raises(NotFoundError):
        await accept_invitation(session, token="expired", user=user)

    assert invitation.status == InvitationStatus.pending
    session.flush.assert_not_called()


@pytest.mark.asyncio
async def test_list_invitations_defaults_to_pending():
    workspace_id = uuid.uuid4()
    invitation = WorkspaceInvitationORM(
        workspace_id=workspace_id,
        email="pending@example.com",
        role=AppRole.viewer,
        token="token",
        invited_by_user_id=uuid.uuid4(),
        status=InvitationStatus.pending,
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )
    invitation.id = uuid.uuid4()
    invitation.created_at = datetime.now(UTC)

    session = AsyncMock()
    result = MagicMock()
    result.scalars.return_value.all.return_value = [invitation]
    session.execute = AsyncMock(return_value=result)

    from app.core.pagination import CursorParams

    page = await list_invitations(session, workspace_id=workspace_id, params=CursorParams(limit=50))

    assert len(page.items) == 1
    assert page.items[0].email == "pending@example.com"
    assert not hasattr(page.items[0], "token")


@pytest.mark.asyncio
async def test_revoke_invitation_sets_status():
    workspace_id = uuid.uuid4()
    invitation_id = uuid.uuid4()
    invitation = WorkspaceInvitationORM(
        workspace_id=workspace_id,
        email="pending@example.com",
        role=AppRole.viewer,
        token="token",
        invited_by_user_id=uuid.uuid4(),
        status=InvitationStatus.pending,
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )
    invitation.id = invitation_id

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=invitation)
    session.flush = AsyncMock()

    revoked = await revoke_invitation(
        session,
        workspace_id=workspace_id,
        invitation_id=invitation_id,
    )

    assert revoked.status == InvitationStatus.revoked


@pytest.mark.asyncio
async def test_revoke_invitation_not_pending_returns_not_found():
    workspace_id = uuid.uuid4()
    invitation = WorkspaceInvitationORM(
        workspace_id=workspace_id,
        email="accepted@example.com",
        role=AppRole.viewer,
        token="token",
        invited_by_user_id=uuid.uuid4(),
        status=InvitationStatus.accepted,
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )

    session = AsyncMock()
    session.scalar = AsyncMock(return_value=invitation)

    with pytest.raises(NotFoundError):
        await revoke_invitation(
            session,
            workspace_id=workspace_id,
            invitation_id=uuid.uuid4(),
        )
