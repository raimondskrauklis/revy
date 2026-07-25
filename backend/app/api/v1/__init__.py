# backend/app/api/v1/__init__.py
"""API v1 router aggregation — add new routers here."""
from fastapi import APIRouter

from app.api.v1 import invitations, items, me, users
from app.api.v1.admin import router as admin_router
from app.api.v1.webhooks import router as webhooks_router
from app.api.v1.workspaces import router as workspaces_router

api_v1_router = APIRouter(prefix="/api/v1")
api_v1_router.include_router(me.router)
api_v1_router.include_router(users.router)
api_v1_router.include_router(items.router)
api_v1_router.include_router(workspaces_router)
api_v1_router.include_router(invitations.router)
api_v1_router.include_router(admin_router)
api_v1_router.include_router(webhooks_router)
