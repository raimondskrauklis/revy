# backend/app/api/v1/webhooks/__init__.py
"""Unauthenticated webhook routers — signature verification in handlers."""
from fastapi import APIRouter

from app.api.v1.webhooks import github, keycloak, stripe

router = APIRouter(prefix="/webhooks", tags=["webhooks"])
router.include_router(stripe.router)
router.include_router(github.router)
router.include_router(keycloak.router)
