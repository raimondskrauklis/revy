# backend/app/main.py
"""FastAPI application factory — wire middleware, health, API v1."""
from __future__ import annotations

from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.api.v1 import api_v1_router
from app.api.v1.health import router as health_router
from app.core.bootstrap import validate_bootstrap_super_admin_config
from app.core.config import settings
from app.core.database import AsyncSessionLocal, close_db, init_db
from app.core.exception_handlers import register_exception_handlers
from app.core.idempotency import IdempotencyStoreMiddleware
from app.core.jwks import jwks_client
from app.core.logging import RequestIdMiddleware, configure_logging, get_logger
from app.core.rate_limit import close_redis
from app.core.sentry import init_sentry

logger = get_logger(__name__)

init_sentry()


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()
    await init_db()
    async with AsyncSessionLocal() as session:
        await validate_bootstrap_super_admin_config(session)
    logger.info("application_started", extra={"environment": settings.environment})
    yield
    await close_db()
    await close_redis()
    await jwks_client.close()
    logger.info("application_stopped", extra={"operation": "shutdown"})


def create_app() -> FastAPI:
    app = FastAPI(
        title="Revy API",
        version=settings.app_version,
        lifespan=lifespan,
        docs_url="/docs" if settings.debug else None,
        redoc_url=None,
    )

    register_exception_handlers(app)

    app.add_middleware(RequestIdMiddleware)
    app.add_middleware(IdempotencyStoreMiddleware)
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        allow_headers=["Authorization", "Content-Type", "Idempotency-Key", "X-Workspace-Id"],
    )

    if settings.environment == "production":
        hosts = [h.strip() for h in settings.trusted_hosts.split(",") if h.strip()]
        app.add_middleware(TrustedHostMiddleware, allowed_hosts=hosts)

    app.include_router(health_router)
    app.include_router(api_v1_router)

    return app


app = create_app()
