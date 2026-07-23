# backend/app/api/v1/admin/__init__.py
"""Platform admin API — super_admin only."""
from fastapi import APIRouter

from app.api.v1.admin import users as admin_users

router = APIRouter(prefix="/admin")
router.include_router(admin_users.router)
