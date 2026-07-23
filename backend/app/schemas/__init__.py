# backend/app/schemas/__init__.py
"""Pydantic request/response models — one module per domain (items.py, me.py, …)."""

from app.schemas.common import ErrorBody, SuccessResponse
from app.schemas.items import ItemCreate, ItemResponse, ItemUpdate
from app.schemas.me import MeResponse, SetActiveWorkspaceRequest

__all__ = [
    "ErrorBody",
    "ItemCreate",
    "ItemResponse",
    "ItemUpdate",
    "MeResponse",
    "SetActiveWorkspaceRequest",
    "SuccessResponse",
]
