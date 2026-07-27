# backend/tests/unit/test_moonshot_review.py
"""Moonshot review client — R4."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core.exceptions import ServiceUnavailableError
from app.integrations.moonshot_review import (
    _chat_completion_body,
    _extract_message_content,
    complete_review,
    parse_review_json,
)


@pytest.mark.asyncio
async def test_complete_review_disabled_raises():
    client = AsyncMock(spec=httpx.AsyncClient)
    with patch("app.integrations.moonshot_review.settings") as mock_settings:
        mock_settings.moonshot_api_key = None
        with pytest.raises(ServiceUnavailableError) as exc:
            await complete_review(client, profile="standard", user_prompt="review this")
    assert exc.value.error_code == "llm_disabled"


@pytest.mark.asyncio
async def test_complete_review_returns_content():
    payload = {
        "choices": [{"message": {"content": json.dumps({"findings": []})}}],
    }
    response = MagicMock()
    response.status_code = 200
    response.raise_for_status = MagicMock()
    response.json.return_value = payload
    client = AsyncMock(spec=httpx.AsyncClient)
    client.post = AsyncMock(return_value=response)

    with patch("app.integrations.moonshot_review.settings") as mock_settings:
        mock_settings.moonshot_api_key = "test-key"
        mock_settings.revy_moonshot_model_for_profile.return_value = "kimi-k2.7-code"
        mock_settings.revy_revision_timeout_seconds.return_value = 60.0
        content = await complete_review(client, profile="standard", user_prompt="review")

    assert json.loads(content)["findings"] == []
    post_kwargs = client.post.call_args.kwargs
    body = post_kwargs["json"]
    assert body["model"] == "kimi-k2.7-code"
    assert "temperature" not in body
    assert "thinking" not in body
    assert "max_completion_tokens" not in body


def test_parse_review_json_valid():
    raw = json.dumps(
        {
            "findings": [
                {
                    "severity": "warning",
                    "category": "bug",
                    "title": "Null check",
                    "message": "Possible null dereference",
                }
            ]
        }
    )
    findings = parse_review_json(raw)
    assert len(findings) == 1
    assert findings[0]["title"] == "Null check"


def test_parse_review_json_invalid_raises():
    with pytest.raises(ValueError):
        parse_review_json(json.dumps([]))


def test_chat_completion_body_k2_7_code_omits_temperature():
    body = _chat_completion_body(
        model="kimi-k2.7-code",
        profile="standard",
        messages=[{"role": "user", "content": "x"}],
    )
    assert "temperature" not in body
    assert "thinking" not in body
    assert "max_completion_tokens" not in body
    assert "reasoning_effort" not in body


def test_chat_completion_body_k3_deep_uses_high_reasoning():
    body = _chat_completion_body(
        model="kimi-k3",
        profile="deep",
        messages=[{"role": "user", "content": "x"}],
    )
    assert "temperature" not in body
    assert body["reasoning_effort"] == "high"
    assert "max_completion_tokens" not in body
    assert "thinking" not in body


def test_chat_completion_body_k3_critical_uses_max_reasoning():
    body = _chat_completion_body(
        model="kimi-k3",
        profile="critical",
        messages=[{"role": "user", "content": "x"}],
    )
    assert body["reasoning_effort"] == "max"
    assert "max_completion_tokens" not in body


def test_chat_completion_body_legacy_uses_temperature():
    body = _chat_completion_body(
        model="moonshot-v1-8k",
        profile="standard",
        messages=[{"role": "user", "content": "x"}],
    )
    assert body["temperature"] == 0.2
    assert "max_completion_tokens" not in body
    assert "thinking" not in body
    assert "reasoning_effort" not in body


def test_extract_message_content_length_finish_reason():
    with pytest.raises(ServiceUnavailableError) as exc:
        _extract_message_content(
            {
                "finish_reason": "length",
                "message": {"content": "", "reasoning_content": "thoughts"},
            },
            model="kimi-k2.7-code",
        )
    assert exc.value.error_code == "llm_error"
    assert "truncated" in exc.value.message
