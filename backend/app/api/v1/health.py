# backend/app/api/v1/health.py
"""Liveness and readiness probes — mount at app root in main.py."""
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import ServiceUnavailableError

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "environment": settings.environment,
    }


@router.get("/ready")
async def readiness_check(db: AsyncSession = Depends(get_db)):
    checks: dict[str, str] = {}
    try:
        await db.execute(text("SELECT 1"))
        checks["database"] = "ok"
    except Exception as exc:
        checks["database"] = str(exc)

    # Extend: redis ping, celery broker — see docs/backend/HEALTH.md
    try:
        from app.core.email import get_email_service

        if settings.email_provider.lower() == "mailgun":
            email_service = get_email_service()
            checks["email"] = "ok" if await email_service.health_check() else "unreachable"
        else:
            checks["email"] = "skipped"
    except Exception as exc:
        checks["email"] = str(exc)

    if any(v != "ok" for v in checks.values()):
        raise ServiceUnavailableError(
            message="Service not ready",
            details={"ready": False, "checks": checks},
        )
    return {"ready": True, "checks": checks}
