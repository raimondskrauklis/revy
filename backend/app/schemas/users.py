# backend/app/schemas/users.py
"""User registration schemas — USER_REGISTRATION.md."""
from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.constants.enums import UserStatus


class CompleteProfileRequest(BaseModel):
    full_name: str = Field(min_length=1, max_length=255)


class PendingUserResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: UUID
    email: str
    full_name: str | None
    status: UserStatus
    created_at: datetime
