# backend/app/schemas/billing.py
"""Billing API schemas — workspace plan and Stripe session URLs."""
from pydantic import BaseModel, Field


class BillingStatus(BaseModel):
    plan: str
    stripe_enabled: bool


class CheckoutSessionRequest(BaseModel):
    plan: str = Field(default="pro", pattern=r"^pro$")


class CheckoutSessionResponse(BaseModel):
    url: str


class PortalSessionResponse(BaseModel):
    url: str
