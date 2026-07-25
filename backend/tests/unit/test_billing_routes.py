# backend/tests/unit/test_billing_routes.py
"""Billing API route handlers — service delegation with mocks."""
import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.api.v1.workspaces.billing import (
    get_workspace_billing,
    post_checkout_session,
    post_portal_session,
)
from app.constants.enums import AppRole, UserStatus
from app.core.auth import CurrentUser
from app.core.exceptions import ForbiddenError, ServiceUnavailableError
from app.schemas.billing import BillingStatus, CheckoutSessionRequest


def _admin_user(workspace_id: uuid.UUID) -> CurrentUser:
    return CurrentUser(
        sub="kc-admin",
        actor_user_id=uuid.uuid4(),
        email="admin@example.com",
        workspace_id=workspace_id,
        role=AppRole.admin,
        status=UserStatus.active,
    )


@pytest.mark.asyncio
async def test_get_workspace_billing_returns_status():
    workspace_id = uuid.uuid4()
    session = AsyncMock()
    expected = BillingStatus(plan="free", stripe_enabled=False)

    with patch(
        "app.api.v1.workspaces.billing.get_billing_status",
        AsyncMock(return_value=expected),
    ):
        response = await get_workspace_billing(
            workspace_id=workspace_id,
            current_user=_admin_user(workspace_id),
            session=session,
        )

    assert response.data.plan == "free"
    assert response.data.stripe_enabled is False


@pytest.mark.asyncio
async def test_get_workspace_billing_denies_other_workspace():
    workspace_id = uuid.uuid4()
    other_workspace_id = uuid.uuid4()
    session = AsyncMock()

    with pytest.raises(ForbiddenError):
        await get_workspace_billing(
            workspace_id=workspace_id,
            current_user=_admin_user(other_workspace_id),
            session=session,
        )


@pytest.mark.asyncio
async def test_post_checkout_session_commits_and_returns_url():
    workspace_id = uuid.uuid4()
    user = _admin_user(workspace_id)
    session = AsyncMock()
    session.get = AsyncMock(return_value=object())
    session.commit = AsyncMock()

    with patch(
        "app.api.v1.workspaces.billing.create_checkout_session",
        AsyncMock(return_value="https://checkout.stripe.test/session"),
    ):
        response = await post_checkout_session(
            workspace_id=workspace_id,
            body=CheckoutSessionRequest(plan="pro"),
            current_user=user,
            _allowed=user,
            session=session,
        )

    session.commit.assert_awaited_once()
    assert response.data.url == "https://checkout.stripe.test/session"


@pytest.mark.asyncio
async def test_post_checkout_session_propagates_billing_disabled():
    workspace_id = uuid.uuid4()
    user = _admin_user(workspace_id)
    session = AsyncMock()
    session.get = AsyncMock(return_value=object())

    with patch(
        "app.api.v1.workspaces.billing.create_checkout_session",
        AsyncMock(
            side_effect=ServiceUnavailableError(
                message="Billing is not configured",
                error_code="billing_disabled",
            )
        ),
    ):
        with pytest.raises(ServiceUnavailableError) as exc:
            await post_checkout_session(
                workspace_id=workspace_id,
                body=CheckoutSessionRequest(plan="pro"),
                current_user=user,
                _allowed=user,
                session=session,
            )

    assert exc.value.error_code == "billing_disabled"


@pytest.mark.asyncio
async def test_post_portal_session_commits_and_returns_url():
    workspace_id = uuid.uuid4()
    user = _admin_user(workspace_id)
    session = AsyncMock()
    session.get = AsyncMock(return_value=object())
    session.commit = AsyncMock()

    with patch(
        "app.api.v1.workspaces.billing.create_portal_session",
        AsyncMock(return_value="https://billing.stripe.test/portal"),
    ):
        response = await post_portal_session(
            workspace_id=workspace_id,
            current_user=user,
            _allowed=user,
            session=session,
        )

    session.commit.assert_awaited_once()
    assert response.data.url == "https://billing.stripe.test/portal"
