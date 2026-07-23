# backend/app/schemas/billing.py
"""Billing API contracts — BILLING.md."""
from __future__ import annotations

from pydantic import BaseModel, Field


class WorkspacePlanResponse(BaseModel):
    plan: str = Field(description="free | pro | enterprise")
    seats_limit: int
    api_calls_per_day_limit: int
