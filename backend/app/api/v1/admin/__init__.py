# backend/app/api/v1/admin/__init__.py
"""Platform admin API — super_admin only."""
from fastapi import APIRouter

from app.api.v1.admin import audit as admin_audit
from app.api.v1.admin import impersonation as admin_impersonation
from app.api.v1.admin import kpis as admin_kpis
from app.api.v1.admin import settings as admin_settings
from app.api.v1.admin import users as admin_users
from app.api.v1.admin import workspaces as admin_workspaces

router = APIRouter(prefix="/admin")
router.include_router(admin_workspaces.router)
router.include_router(admin_impersonation.router)
router.include_router(admin_kpis.router)
router.include_router(admin_audit.router)
router.include_router(admin_settings.router)
router.include_router(admin_users.router)
