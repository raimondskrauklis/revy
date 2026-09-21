# backend/tests/unit/test_stripe_credit_mutations.py
"""Stripe webhook credit mutations — upgrade/downgrade sets review_run_limit."""
from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest

from app.models.workspaces import WorkspaceORM
from app.services.billing import apply_subscription_event


@pytest.fixture
def workspace():
    ws = WorkspaceORM(slug="test-ws", name="Test", plan="pro", review_run_limit=None)
    ws.id = uuid.uuid4()
    return ws


@pytest.fixture
def mock_session(workspace):
    session = AsyncMock()
    session.get = AsyncMock(return_value=workspace)
    session.scalar = AsyncMock()
    session.flush = AsyncMock()
    return session


@pytest.mark.asyncio
async def test_checkout_completed_upgrade_sets_limit_null(mock_session, workspace):
    """checkout.session.completed for pro plan → review_run_limit = None (unlimited)."""
    event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "payment_status": "paid",
                "customer": "cus_test123",
                "metadata": {
                    "workspace_id": str(workspace.id),
                    "plan": "pro",
                    "actor_user_id": str(uuid.uuid4()),
                },
            },
        },
    }

    with patch("app.services.billing.settings.stripe_enabled", True):
        await apply_subscription_event(mock_session, event)

    assert workspace.review_run_limit is None


@pytest.mark.asyncio
async def test_subscription_deleted_downgrade_sets_limit_25(mock_session, workspace):
    """customer.subscription.deleted → review_run_limit = 25."""
    workspace.stripe_customer_id = "cus_test123"


    event = {
        "type": "customer.subscription.deleted",
        "data": {"object": {"customer": "cus_test123"}},
    }

    with (
        patch("app.services.billing.settings.stripe_enabled", True),
        patch(
            "app.services.billing._workspace_by_customer_id",
            new_callable=AsyncMock,
            return_value=workspace,
        ),
    ):
        await apply_subscription_event(mock_session, event)

    assert workspace.review_run_limit == 25


@pytest.mark.asyncio
async def test_subscription_updated_to_pro_sets_limit_null(mock_session, workspace):
    """customer.subscription.updated with pro plan → review_run_limit = None."""
    workspace.stripe_customer_id = "cus_test123"
    workspace.plan = "free"
    workspace.review_run_limit = 25

    event = {
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "customer": "cus_test123",
                "status": "active",
                "items": {
                    "data": [
                        {"price": {"id": "price_pro_test"}}
                    ]
                },
            },
        },
    }

    with (
        patch("app.services.billing.settings.stripe_enabled", True),
        patch("app.services.billing.settings.stripe_price_pro", "price_pro_test"),
        patch(
            "app.services.billing._workspace_by_customer_id",
            new_callable=AsyncMock,
            return_value=workspace,
        ),
    ):
        await apply_subscription_event(mock_session, event)

    assert workspace.plan == "pro"
    assert workspace.review_run_limit is None