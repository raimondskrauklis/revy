# backend/app/constants/model_policy.py
"""Model policy role identifiers — MODEL_POLICY program."""
from enum import Enum


class ModelRole(str, Enum):
    """Pipeline slots resolved by ``resolve_model``."""

    reviewer_standard = "reviewer_standard"
    reviewer_deep = "reviewer_deep"
    reviewer_critical = "reviewer_critical"
    judge = "judge"
