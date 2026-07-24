# backend/app/api/v1/workspaces/__init__.py
"""Workspace-scoped routes — nested resources (invitations, settings, …)."""
from fastapi import APIRouter

from app.api.v1.workspaces import installations, invitations

router = APIRouter(prefix="/workspaces", tags=["workspaces"])
router.include_router(invitations.router)
router.include_router(installations.router)
