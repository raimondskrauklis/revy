# backend/app/core/exception_handlers.py
"""Global exception handlers — flat error JSON per docs/errors/OBSERVABILITY.md."""

from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

from app.core.exceptions import PlatformException
from app.core.logging import get_logger
from app.core.sentry import capture_exception

logger = get_logger(__name__)


async def platform_exception_handler(
    request: Request, exc: PlatformException
) -> JSONResponse:
    if exc.http_status_code >= 500:
        logger.error("platform_error", extra={"error_message": exc.message}, exc_info=True)
        capture_exception(exc)
    else:
        logger.info(
            "platform_error",
            extra={"error_message": exc.message, "code": exc.error_code},
        )

    content: dict = {
        "error": exc.error_code,
        "message": exc.message,
        "details": exc.details or {},
    }
    if exc.field:
        content["field"] = exc.field

    return JSONResponse(status_code=exc.http_status_code, content=content)


async def sqlalchemy_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    logger.error("database_error", exc_info=True)
    capture_exception(exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "database_error",
            "message": "A database error occurred",
        },
    )


async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    logger.error("unexpected_error", exc_info=True)
    capture_exception(exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": "internal_server_error",
            "message": "An unexpected error occurred",
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    app.add_exception_handler(PlatformException, platform_exception_handler)
    app.add_exception_handler(SQLAlchemyError, sqlalchemy_exception_handler)
    app.add_exception_handler(Exception, general_exception_handler)
