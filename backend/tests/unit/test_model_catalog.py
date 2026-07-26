# backend/tests/unit/test_model_catalog.py
"""Model catalog service — MODEL_POLICY M2."""
from unittest.mock import patch

from app.constants.model_policy import ModelRole
from app.services.model_catalog import build_model_catalog, is_valid_catalog_entry


def test_build_model_catalog_includes_moonshot_when_configured():
    with patch("app.services.model_catalog.settings") as mock_settings:
        mock_settings.moonshot_api_key = "key"
        mock_settings.anthropic_api_key = None
        mock_settings.bedrock_enabled.return_value = False
        mock_settings.effective_judge_provider = "anthropic"
        mock_settings.revy_anthropic_model = "claude-sonnet-4-20250514"
        catalog = build_model_catalog()
    assert any(
        item.provider == "moonshot" for item in catalog[ModelRole.reviewer_standard.value]
    )


def test_is_valid_catalog_entry_accepts_known_model():
    with patch("app.services.model_catalog.settings") as mock_settings:
        mock_settings.moonshot_api_key = "key"
        mock_settings.anthropic_api_key = None
        mock_settings.bedrock_enabled.return_value = False
        mock_settings.effective_judge_provider = "anthropic"
        assert is_valid_catalog_entry(
            role=ModelRole.reviewer_standard,
            provider="moonshot",
            model_id="kimi-k2.7-code",
        )


def test_is_valid_catalog_entry_rejects_unknown_model():
    with patch("app.services.model_catalog.settings") as mock_settings:
        mock_settings.moonshot_api_key = "key"
        mock_settings.anthropic_api_key = None
        mock_settings.bedrock_enabled.return_value = False
        mock_settings.effective_judge_provider = "anthropic"
        assert not is_valid_catalog_entry(
            role=ModelRole.reviewer_standard,
            provider="moonshot",
            model_id="unknown-model",
        )
