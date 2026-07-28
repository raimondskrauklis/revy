# backend/tests/unit/test_bedrock_review.py
"""Bedrock review client — MODEL_POLICY M1."""
import json
from unittest.mock import AsyncMock, patch

import pytest

from app.core.exceptions import ServiceUnavailableError
from app.integrations.bedrock_review import complete_review, judge_finding


@pytest.mark.asyncio
async def test_complete_review_disabled_raises():
    with patch("app.integrations.bedrock_review.settings") as mock_settings:
        mock_settings.bedrock_enabled.return_value = False
        with pytest.raises(ServiceUnavailableError) as exc:
            await complete_review(
                user_prompt="review",
                model_id="anthropic.claude-sonnet-4-20250514-v1:0",
                region="eu-central-1",
            )
    assert exc.value.error_code == "llm_disabled"


@pytest.mark.asyncio
async def test_complete_review_returns_content():
    payload = {
        "output": {"message": {"content": [{"text": json.dumps({"findings": []})}]}},
    }
    with (
        patch("app.integrations.bedrock_review.settings") as mock_settings,
        patch("app.integrations.bedrock_review.asyncio.to_thread", new=AsyncMock(return_value=payload)) as to_thread,
    ):
        mock_settings.bedrock_enabled.return_value = True
        mock_settings.aws_region = "eu-central-1"
        mock_settings.revy_revision_timeout_standard_seconds = 900
        content = await complete_review(
            user_prompt="review",
            model_id="anthropic.claude-sonnet-4-20250514-v1:0",
            region="eu-central-1",
        )
    assert json.loads(content)["findings"] == []
    to_thread.assert_awaited_once()


@pytest.mark.asyncio
async def test_judge_finding_returns_payload():
    payload = {
        "output": {
            "message": {
                "content": [{"text": json.dumps({"outcome": "upheld", "notes": "valid"})}],
            },
        },
    }
    with (
        patch("app.integrations.bedrock_review.settings") as mock_settings,
        patch("app.integrations.bedrock_review.asyncio.to_thread", new=AsyncMock(return_value=payload)),
    ):
        mock_settings.bedrock_enabled.return_value = True
        mock_settings.aws_region = "eu-central-1"
        mock_settings.revy_revision_timeout_standard_seconds = 900
        result = await judge_finding(
            user_prompt="judge",
            model_id="anthropic.claude-sonnet-4-20250514-v1:0",
            region="eu-central-1",
        )
    assert result["outcome"] == "upheld"


@pytest.mark.asyncio
async def test_judge_finding_raises_judge_parse_error_on_invalid_json():
    from app.integrations.judge_llm_errors import JudgeParseError

    payload = {
        "output": {
            "message": {
                "content": [{"text": "prose only, no json"}],
            },
        },
    }
    with (
        patch("app.integrations.bedrock_review.settings") as mock_settings,
        patch("app.integrations.bedrock_review.asyncio.to_thread", new=AsyncMock(return_value=payload)),
    ):
        mock_settings.bedrock_enabled.return_value = True
        mock_settings.aws_region = "eu-central-1"
        mock_settings.revy_revision_timeout_standard_seconds = 900
        with pytest.raises(JudgeParseError) as exc_info:
            await judge_finding(
                user_prompt="judge",
                model_id="anthropic.claude-sonnet-4-20250514-v1:0",
                region="eu-central-1",
            )
    assert exc_info.value.code == "judge_json_invalid"
    assert "prose only" in exc_info.value.response_text


@pytest.mark.asyncio
async def test_complete_review_timeout_maps_to_service_unavailable():
    with (
        patch("app.integrations.bedrock_review.settings") as mock_settings,
        patch(
            "app.integrations.bedrock_review.asyncio.wait_for",
            new=AsyncMock(side_effect=TimeoutError()),
        ),
    ):
        mock_settings.bedrock_enabled.return_value = True
        mock_settings.revy_revision_timeout_standard_seconds = 900
        with pytest.raises(ServiceUnavailableError) as exc:
            await complete_review(
                user_prompt="review",
                model_id="anthropic.claude-sonnet-4-20250514-v1:0",
                region="eu-central-1",
            )
    assert exc.value.error_code == "llm_error"


@pytest.mark.asyncio
async def test_judge_finding_timeout_maps_to_service_unavailable():
    with (
        patch("app.integrations.bedrock_review.settings") as mock_settings,
        patch(
            "app.integrations.bedrock_review.asyncio.wait_for",
            new=AsyncMock(side_effect=TimeoutError()),
        ),
    ):
        mock_settings.bedrock_enabled.return_value = True
        mock_settings.revy_revision_timeout_standard_seconds = 900
        with pytest.raises(ServiceUnavailableError) as exc:
            await judge_finding(
                user_prompt="judge",
                model_id="anthropic.claude-sonnet-4-20250514-v1:0",
                region="eu-central-1",
            )
    assert exc.value.error_code == "llm_error"
