# backend/app/services/billing.py
"""Workspace billing — Stripe Checkout, Portal, and plan sync."""
from __future__ import annotations

from typing import Any
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.constants.enums import AppRole
from app.core.config import settings
from app.core.exceptions import (
    BillingWebhookError,
    NotFoundError,
    ServiceUnavailableError,
    ValidationError,
)
from app.core.logging import get_logger
from app.integrations.stripe_client import StripeClientProtocol, get_stripe_client
from app.models.stripe_webhook_event import StripeWebhookEventORM
from app.models.workspace_memberships import WorkspaceMembershipORM
from app.models.workspaces import WorkspaceORM
from app.schemas.billing import BillingStatus
from app.services.audit_service import record_audit

logger = get_logger(__name__)

VALID_PLANS = frozenset({"free", "pro"})


def effective_plan(workspace: WorkspaceORM) -> str:
    plan = workspace.plan or "free"
    return plan if plan in VALID_PLANS else "free"


def _checkout_success_url() -> str:
    if settings.stripe_checkout_success_url:
        return settings.stripe_checkout_success_url
    base = (settings.app_public_url or "http://localhost:5173").rstrip("/")
    return f"{base}/settings/billing?checkout=success"


def _checkout_cancel_url() -> str:
    if settings.stripe_checkout_cancel_url:
        return settings.stripe_checkout_cancel_url
    base = (settings.app_public_url or "http://localhost:5173").rstrip("/")
    return f"{base}/settings/billing?checkout=cancel"


def _portal_return_url() -> str:
    base = (settings.app_public_url or "http://localhost:5173").rstrip("/")
    return f"{base}/settings/billing"


def _require_stripe_enabled() -> None:
    if not settings.stripe_enabled:
        raise ServiceUnavailableError(
            message="Billing is not configured",
            error_code="billing_disabled",
        )


async def get_billing_status(session: AsyncSession, workspace_id: UUID) -> BillingStatus:
    workspace = await session.get(WorkspaceORM, workspace_id)
    if workspace is None:
        raise NotFoundError("Workspace not found")
    return BillingStatus(
        plan=effective_plan(workspace),
        stripe_enabled=settings.stripe_enabled,
    )


async def _ensure_stripe_customer(
    session: AsyncSession,
    workspace: WorkspaceORM,
    *,
    stripe_client: StripeClientProtocol,
    actor_email: str | None,
) -> str:
    if workspace.stripe_customer_id:
        return workspace.stripe_customer_id

    customer_id = stripe_client.create_customer(
        email=actor_email or f"workspace-{workspace.id}@billing.local",
        name=workspace.name,
        metadata={"workspace_id": str(workspace.id)},
    )
    workspace.stripe_customer_id = customer_id
    await session.flush()
    return customer_id


async def create_checkout_session(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    plan: str,
    actor_user_id: UUID,
    actor_email: str | None,
    impersonator_user_id: UUID | None = None,
    stripe_client: StripeClientProtocol | None = None,
) -> str:
    _require_stripe_enabled()
    if plan != "pro":
        raise ValidationError(message="Unsupported plan", field="plan")
    if not settings.stripe_price_pro:
        raise ServiceUnavailableError(
            message="Billing is not configured",
            error_code="billing_disabled",
        )

    workspace = await session.get(WorkspaceORM, workspace_id)
    if workspace is None:
        raise NotFoundError("Workspace not found")

    client = stripe_client or get_stripe_client()
    customer_id = await _ensure_stripe_customer(
        session,
        workspace,
        stripe_client=client,
        actor_email=actor_email,
    )
    metadata = {
        "workspace_id": str(workspace_id),
        "plan": plan,
        "actor_user_id": str(actor_user_id),
    }
    url = client.create_checkout_session(
        customer_id=customer_id,
        price_id=settings.stripe_price_pro,
        success_url=_checkout_success_url(),
        cancel_url=_checkout_cancel_url(),
        metadata=metadata,
    )
    await record_audit(
        session,
        actor_user_id=actor_user_id,
        impersonator_user_id=impersonator_user_id,
        workspace_id=workspace_id,
        action="billing.checkout_started",
        resource_type="workspace",
        resource_id=str(workspace_id),
        metadata={"plan": plan},
    )
    return url


async def create_portal_session(
    session: AsyncSession,
    *,
    workspace_id: UUID,
    actor_user_id: UUID,
    impersonator_user_id: UUID | None = None,
    stripe_client: StripeClientProtocol | None = None,
) -> str:
    _require_stripe_enabled()

    workspace = await session.get(WorkspaceORM, workspace_id)
    if workspace is None:
        raise NotFoundError("Workspace not found")
    if not workspace.stripe_customer_id:
        raise ValidationError(
            message="No billing customer for this workspace",
            field="stripe_customer_id",
        )

    client = stripe_client or get_stripe_client()
    url = client.create_portal_session(
        customer_id=workspace.stripe_customer_id,
        return_url=_portal_return_url(),
    )
    await record_audit(
        session,
        actor_user_id=actor_user_id,
        impersonator_user_id=impersonator_user_id,
        workspace_id=workspace_id,
        action="billing.portal_opened",
        resource_type="workspace",
        resource_id=str(workspace_id),
        metadata={"plan": effective_plan(workspace)},
    )
    return url


async def _billing_actor_id(session: AsyncSession, workspace_id: UUID) -> UUID:
    stmt = (
        select(WorkspaceMembershipORM.user_id)
        .where(
            WorkspaceMembershipORM.workspace_id == workspace_id,
            WorkspaceMembershipORM.role == AppRole.admin,
        )
        .limit(1)
    )
    actor_id = await session.scalar(stmt)
    if actor_id is None:
        raise NotFoundError("No workspace admin found for billing audit")
    return actor_id


async def _update_workspace_plan(
    session: AsyncSession,
    *,
    workspace: WorkspaceORM,
    new_plan: str,
    actor_user_id: UUID | None = None,
    stripe_customer_id: str | None = None,
) -> bool:
    old_plan = effective_plan(workspace)
    normalized = new_plan if new_plan in VALID_PLANS else "free"
    changed = old_plan != normalized or (
        stripe_customer_id is not None and workspace.stripe_customer_id != stripe_customer_id
    )
    workspace.plan = normalized
    if stripe_customer_id is not None:
        workspace.stripe_customer_id = stripe_customer_id
    await session.flush()

    if changed and old_plan != normalized:
        audit_actor = actor_user_id or await _billing_actor_id(session, workspace.id)
        await record_audit(
            session,
            actor_user_id=audit_actor,
            workspace_id=workspace.id,
            action="billing.subscription_updated",
            resource_type="workspace",
            resource_id=str(workspace.id),
            metadata={"old_plan": old_plan, "new_plan": normalized},
        )
    return changed


def _plan_from_subscription(subscription: dict[str, Any]) -> str:
    if not settings.stripe_price_pro:
        return "free"
    status = subscription.get("status")
    if status not in {"active", "trialing", "past_due"}:
        return "free"
    items = subscription.get("items", {}).get("data", [])
    for item in items:
        price = item.get("price") or {}
        price_id = price.get("id")
        if price_id == settings.stripe_price_pro:
            return "pro"
    return "free"


async def _workspace_by_customer_id(
    session: AsyncSession,
    customer_id: str,
) -> WorkspaceORM | None:
    stmt = select(WorkspaceORM).where(WorkspaceORM.stripe_customer_id == customer_id).limit(1)
    return await session.scalar(stmt)


async def apply_subscription_event(
    session: AsyncSession,
    event: Any,
    *,
    stripe_client: StripeClientProtocol | None = None,
) -> None:
    _ = stripe_client
    event_type = event["type"]
    data_object = event["data"]["object"]

    if event_type == "checkout.session.completed":
        payment_status = data_object.get("payment_status")
        if payment_status not in {"paid", "no_payment_required"}:
            raise BillingWebhookError(
                message=f"Checkout session not paid: {payment_status!r}",
            )
        metadata = data_object.get("metadata") or {}
        workspace_id_raw = metadata.get("workspace_id")
        plan = metadata.get("plan") or "pro"
        actor_raw = metadata.get("actor_user_id")
        if not workspace_id_raw:
            raise BillingWebhookError(message="Checkout metadata missing workspace_id")
        workspace = await session.get(WorkspaceORM, UUID(workspace_id_raw))
        if workspace is None:
            raise BillingWebhookError(message="Workspace not found for checkout metadata")
        actor_user_id = UUID(actor_raw) if actor_raw else None
        customer_id = data_object.get("customer")
        await _update_workspace_plan(
            session,
            workspace=workspace,
            new_plan=plan,
            actor_user_id=actor_user_id,
            stripe_customer_id=customer_id if isinstance(customer_id, str) else None,
        )
        return

    if event_type in {"customer.subscription.updated", "customer.subscription.deleted"}:
        customer_id = data_object.get("customer")
        if not isinstance(customer_id, str):
            raise BillingWebhookError(message="Subscription event missing customer id")
        workspace = await _workspace_by_customer_id(session, customer_id)
        if workspace is None:
            metadata = data_object.get("metadata") or {}
            workspace_id_raw = metadata.get("workspace_id")
            if workspace_id_raw:
                workspace = await session.get(WorkspaceORM, UUID(workspace_id_raw))
        if workspace is None:
            logger.warning(
                "stripe_subscription_orphan",
                extra={"customer_id": customer_id, "event_type": event_type},
            )
            return
        new_plan = "free" if event_type == "customer.subscription.deleted" else _plan_from_subscription(
            data_object
        )
        await _update_workspace_plan(session, workspace=workspace, new_plan=new_plan)
        return

    if event_type in {"invoice.paid", "invoice.payment_failed"}:
        customer_id = data_object.get("customer")
        if not isinstance(customer_id, str):
            return
        workspace = await _workspace_by_customer_id(session, customer_id)
        if workspace is None:
            return
        actor_id = await _billing_actor_id(session, workspace.id)
        await record_audit(
            session,
            actor_user_id=actor_id,
            workspace_id=workspace.id,
            action=f"billing.{event_type.replace('.', '_')}",
            resource_type="workspace",
            resource_id=str(workspace.id),
            metadata={
                "invoice_id": data_object.get("id"),
                "amount_due": data_object.get("amount_due"),
                "status": data_object.get("status"),
            },
        )


async def try_record_webhook_event(
    session: AsyncSession,
    *,
    event_id: str,
    event_type: str,
) -> bool:
    existing = await session.get(StripeWebhookEventORM, event_id)
    if existing is not None:
        return False
    session.add(StripeWebhookEventORM(event_id=event_id, event_type=event_type))
    await session.flush()
    return True
