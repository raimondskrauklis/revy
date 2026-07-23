# backend/app/schemas/common.py
"""Shared API response envelopes — docs/backend/API.md."""
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class SuccessResponse(BaseModel, Generic[T]):
    success: bool = True
    data: T


class ErrorBody(BaseModel):
    error: str
    message: str
    details: dict = Field(default_factory=dict)
    field: str | None = None
