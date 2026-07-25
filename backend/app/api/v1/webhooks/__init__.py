# backend/app/api/v1/webhooks/__init__.py
"""Unauthenticated webhook routers — signature verification in handlers."""
from fastapi import APIRouter

from app.api.v1.webhooks import stripe

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
router.include_router(stripe.router)
