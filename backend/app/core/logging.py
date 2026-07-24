# backend/app/core/logging.py
"""Structured logging and request_id middleware — driven by LOG_LEVEL / LOG_FORMAT."""
from __future__ import annotations

import json
import logging
import sys
import time
import uuid
from contextvars import ContextVar
from datetime import UTC, datetime
from typing import Any

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

request_id_ctx: ContextVar[str | None] = ContextVar("request_id", default=None)

_VALID_LOG_FORMATS = frozenset({"json", "console"})
_LOG_RECORD_RESERVED = frozenset(
    {
        "args",
        "asctime",
        "created",
        "exc_info",
        "exc_text",
        "filename",
        "funcName",
        "levelname",
        "levelno",
        "lineno",
        "module",
        "msecs",
        "message",
        "msg",
        "name",
        "pathname",
        "process",
        "processName",
        "relativeCreated",
        "stack_info",
        "taskName",
        "thread",
        "threadName",
    }
)


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "timestamp": datetime.now(UTC).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        rid = request_id_ctx.get()
        if rid:
            payload["request_id"] = rid
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        for key, value in record.__dict__.items():
            if key in _LOG_RECORD_RESERVED or key in payload:
                continue
            payload[key] = value
        return json.dumps(payload, ensure_ascii=False)


class ConsoleFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        rid = request_id_ctx.get()
        prefix = f"{datetime.now(UTC).isoformat()} [{record.levelname}] {record.name}"
        if rid:
            prefix += f" request_id={rid}"
        message = record.getMessage()
        if record.exc_info:
            message = f"{message}\n{self.formatException(record.exc_info)}"
        return f"{prefix}: {message}"


def _resolve_log_level(name: str) -> int:
    resolved = logging.getLevelNamesMapping().get(name.upper())
    if resolved is None:
        msg = f"Invalid LOG_LEVEL: {name}"
        raise ValueError(msg)
    return resolved


def configure_logging() -> None:
    """Apply root logger from settings.log_level and settings.log_format."""
    from app.core.config import settings

    log_format = settings.log_format.strip().lower()
    if log_format not in _VALID_LOG_FORMATS:
        msg = f"Invalid LOG_FORMAT: {settings.log_format} (expected json or console)"
        raise ValueError(msg)

    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(ConsoleFormatter() if log_format == "console" else JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(_resolve_log_level(settings.log_level))


def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)


class RequestIdMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next) -> Response:
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
        token = request_id_ctx.set(request_id)
        start = time.perf_counter()
        try:
            response = await call_next(request)
        finally:
            request_id_ctx.reset(token)
        duration_ms = int((time.perf_counter() - start) * 1000)
        get_logger("http").info(
            "request_completed",
            extra={
                "method": request.method,
                "path": request.url.path,
                "status_code": response.status_code,
                "duration_ms": duration_ms,
            },
        )
        response.headers["X-Request-ID"] = request_id
        return response
