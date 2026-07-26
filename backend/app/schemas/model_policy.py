# backend/app/schemas/model_policy.py
"""Model policy API schemas — MODEL_POLICY M2."""

from __future__ import annotations

from pydantic import BaseModel, Field


class ModelPolicyEntry(BaseModel):
    provider: str
    model_id: str
    region: str | None = None


class ModelPolicyPatch(BaseModel):
    reviewer_standard: ModelPolicyEntry | None = Field(default=None)
    reviewer_deep: ModelPolicyEntry | None = Field(default=None)
    reviewer_critical: ModelPolicyEntry | None = Field(default=None)
    judge: ModelPolicyEntry | None = Field(default=None)


class ModelPolicyResponse(BaseModel):
    overrides: dict[str, ModelPolicyEntry | None]
    effective: dict[str, ModelPolicyEntry]


class ModelCatalogItem(BaseModel):
    provider: str
    model_id: str
    display_name: str
    region: str | None = None


class ModelCatalogResponse(BaseModel):
    roles: dict[str, list[ModelCatalogItem]]
