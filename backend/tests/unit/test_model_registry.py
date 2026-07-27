# backend/tests/unit/test_model_registry.py
"""Model registry helpers."""
from app.constants.model_registry import normalize_provider_slug


def test_normalize_provider_slug_strips_and_lowercases() -> None:
    assert normalize_provider_slug(" Moonshot ") == "moonshot"
    assert normalize_provider_slug("BEDROCK") == "bedrock"
