# backend/tests/unit/test_billing_service.py
"""Billing service — plan state, Checkout, Portal, webhook apply."""
import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.constants.enums import WorkspaceStatus
from app.core.exceptions import (
    BillingWebhookError,
    NotFoundError,
    ServiceUnavailableError,
    ValidationError,
)
from app.models.workspaces import WorkspaceORM
from app.services.billing import (
    apply_subscription_event,
    create_checkout_session,
    create_portal_session,
    effective_plan,
    get_billing_status,
    try_record_webhook_event,
)


def _workspace(*, plan: str | None = None, customer_id: str | None = None) -> WorkspaceORM:
    workspace = WorkspaceORM(
        slug="acme",
        name="Acme Corp",
        status=WorkspaceStatus.active,
        plan=plan,
        stripe_customer_id=customer_id,
    )
    workspace.id = uuid.uuid4()
    return workspace


class FakeStripeClient:
    def __init__(self) -> None:
        self.checkout_calls: list[dict] = []

    def create_customer(self, *, email: str, name: str, metadata: dict[str, str]) -> str:
        return "cus_test_123"

    def create_checkout_session(self, **kwargs) -> str:
        self.checkout_calls.append(kwargs)
        return "https://checkout.stripe.test/session"

    def create_portal_session(self, *, customer_id: str, return_url: str) -> str:
        return "https://billing.stripe.test/portal"

    def construct_webhook_event(self, payload: bytes, signature: str):
        return payload


@pytest.mark.asyncio
async def test_effective_plan_treats_null_as_free():
    assert effective_plan(_workspace(plan=None)) == "free"
    assert effective_plan(_workspace(plan="pro")) == "pro"


@pytest.mark.asyncio
async def test_get_billing_status_returns_plan_and_flag():
    workspace = _workspace(plan="pro")
    session = AsyncMock()
    session.get = AsyncMock(return_value=workspace)

    with patch("app.services.billing.settings") as mock_settings:
        mock_settings.stripe_enabled = False
        status = await get_billing_status(session, workspace.id)

    assert status.plan == "pro"
    assert status.stripe_enabled is False


@pytest.mark.asyncio
async def test_get_billing_status_workspace_not_found():
    session = AsyncMock()
    session.get = AsyncMock(return_value=None)

    with pytest.raises(NotFoundError):
        await get_billing_status(session, uuid.uuid4())


@pytest.mark.asyncio
async def test_create_checkout_session_disabled_raises():
    session = AsyncMock()
    with patch("app.services.billing.settings") as mock_settings:
        mock_settings.stripe_enabled = False
        with pytest.raises(ServiceUnavailableError) as exc:
            await create_checkout_session(
                session,
                workspace_id=uuid.uuid4(),
                plan="pro",
                actor_user_id=uuid.uuid4(),
                actor_email="admin@example.com",
            )
    assert exc.value.error_code == "billing_disabled"


@pytest.mark.asyncio
async def test_create_checkout_session_creates_customer_and_audit():
    workspace = _workspace()
    actor_id = uuid.uuid4()
    stripe_client = FakeStripeClient()
    session = AsyncMock()
    session.get = AsyncMock(return_value=workspace)
    session.add = MagicMock()
    session.flush = AsyncMock()

    with patch("app.services.billing.settings") as mock_settings:
        mock_settings.stripe_enabled = True
        mock_settings.stripe_price_pro = "price_pro_test"
        mock_settings.stripe_checkout_success_url = None
        mock_settings.stripe_checkout_cancel_url = None
        mock_settings.app_public_url = "http://localhost:5173"
        url = await create_checkout_session(
            session,
            workspace_id=workspace.id,
            plan="pro",
            actor_user_id=actor_id,
            actor_email="admin@example.com",
            stripe_client=stripe_client,
        )

    assert url == "https://checkout.stripe.test/session"
    assert workspace.stripe_customer_id == "cus_test_123"
    session.add.assert_called()


@pytest.mark.asyncio
async def test_create_checkout_session_rejects_non_pro_plan():
    session = AsyncMock()
    with patch("app.services.billing.settings") as mock_settings:
        mock_settings.stripe_enabled = True
        with pytest.raises(ValidationError):
            await create_checkout_session(
                session,
                workspace_id=uuid.uuid4(),
                plan="enterprise",
                actor_user_id=uuid.uuid4(),
                actor_email="admin@example.com",
                stripe_client=FakeStripeClient(),
            )


@pytest.mark.asyncio
async def test_create_portal_session_requires_customer():
    workspace = _workspace()
    session = AsyncMock()
    session.get = AsyncMock(return_value=workspace)

    with patch("app.services.billing.settings") as mock_settings:
        mock_settings.stripe_enabled = True
        with pytest.raises(ValidationError):
            await create_portal_session(
                session,
                workspace_id=workspace.id,
                actor_user_id=uuid.uuid4(),
                stripe_client=FakeStripeClient(),
            )


@pytest.mark.asyncio
async def test_create_portal_session_returns_url():
    workspace = _workspace(customer_id="cus_existing")
    actor_id = uuid.uuid4()
    session = AsyncMock()
    session.get = AsyncMock(return_value=workspace)
    session.add = MagicMock()
    session.flush = AsyncMock()

    with patch("app.services.billing.settings") as mock_settings:
        mock_settings.stripe_enabled = True
        mock_settings.app_public_url = "http://localhost:5173"
        url = await create_portal_session(
            session,
            workspace_id=workspace.id,
            actor_user_id=actor_id,
            stripe_client=FakeStripeClient(),
        )

    assert url == "https://billing.stripe.test/portal"


@pytest.mark.asyncio
async def test_try_record_webhook_event_is_idempotent():
    session = AsyncMock()
    session.get = AsyncMock(side_effect=[None, MagicMock()])
    session.add = MagicMock()
    session.flush = AsyncMock()

    first = await try_record_webhook_event(
        session, event_id="evt_1", event_type="checkout.session.completed"
    )
    second = await try_record_webhook_event(
        session, event_id="evt_1", event_type="checkout.session.completed"
    )

    assert first is True
    assert second is False


@pytest.mark.asyncio
async def test_apply_subscription_event_checkout_completed():
    workspace = _workspace()
    actor_id = uuid.uuid4()
    session = AsyncMock()
    session.get = AsyncMock(return_value=workspace)
    session.scalar = AsyncMock(return_value=None)
    session.flush = AsyncMock()
    session.add = MagicMock()

    event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer": "cus_new",
                "payment_status": "paid",
                "metadata": {
                    "workspace_id": str(workspace.id),
                    "plan": "pro",
                    "actor_user_id": str(actor_id),
                },
            }
        },
    }

    with patch("app.services.billing.settings") as mock_settings:
        mock_settings.stripe_price_pro = "price_pro_test"
        await apply_subscription_event(session, event)

    assert workspace.plan == "pro"
    assert workspace.stripe_customer_id == "cus_new"


@pytest.mark.asyncio
async def test_apply_subscription_event_subscription_deleted_sets_free():
    workspace = _workspace(plan="pro", customer_id="cus_existing")
    admin_id = uuid.uuid4()
    session = AsyncMock()
    session.get = AsyncMock(return_value=workspace)
    session.scalar = AsyncMock(side_effect=[workspace, admin_id])
    session.flush = AsyncMock()
    session.add = MagicMock()

    event = {
        "type": "customer.subscription.deleted",
        "data": {"object": {"customer": "cus_existing", "status": "canceled"}},
    }

    with patch("app.services.billing.settings") as mock_settings:
        mock_settings.stripe_price_pro = "price_pro_test"
        await apply_subscription_event(session, event)

    assert workspace.plan == "free"


@pytest.mark.asyncio
async def test_apply_subscription_event_checkout_unpaid_raises():
    workspace = _workspace()
    session = AsyncMock()
    session.get = AsyncMock(return_value=workspace)

    event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer": "cus_new",
                "payment_status": "unpaid",
                "metadata": {
                    "workspace_id": str(workspace.id),
                    "plan": "pro",
                },
            }
        },
    }

    with pytest.raises(BillingWebhookError):
        await apply_subscription_event(session, event)


@pytest.mark.asyncio
async def test_apply_subscription_event_checkout_missing_workspace_raises():
    session = AsyncMock()

    event = {
        "type": "checkout.session.completed",
        "data": {
            "object": {
                "customer": "cus_new",
                "payment_status": "paid",
                "metadata": {"plan": "pro"},
            }
        },
    }

    with pytest.raises(BillingWebhookError):
        await apply_subscription_event(session, event)


@pytest.mark.asyncio
async def test_plan_from_subscription_requires_pro_price():
    workspace = _workspace(plan="free", customer_id="cus_existing")
    admin_id = uuid.uuid4()
    session = AsyncMock()
    session.get = AsyncMock(return_value=workspace)
    session.scalar = AsyncMock(side_effect=[workspace, admin_id])
    session.flush = AsyncMock()
    session.add = MagicMock()

    event = {
        "type": "customer.subscription.updated",
        "data": {
            "object": {
                "customer": "cus_existing",
                "status": "active",
                "items": {
                    "data": [
                        {"price": {"id": "price_legacy_other"}},
                    ]
                },
            }
        },
    }

    with patch("app.services.billing.settings") as mock_settings:
        mock_settings.stripe_price_pro = "price_pro_test"
        await apply_subscription_event(session, event)

    assert workspace.plan == "free"


@pytest.mark.asyncio
async def test_apply_subscription_event_orphan_customer_returns_without_error():
    session = AsyncMock()
    session.scalar = AsyncMock(return_value=None)
    session.get = AsyncMock(return_value=None)

    event = {
        "type": "customer.subscription.deleted",
        "data": {"object": {"customer": "cus_orphan", "status": "canceled"}},
    }

    await apply_subscription_event(session, event)

    session.flush.assert_not_awaited()
