# backend/tests/unit/test_moonshot_review.py
"""Moonshot review client — R4."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core.exceptions import ServiceUnavailableError
from app.integrations.moonshot_review import (
    ISSUE_COMMENT_FORMAT_SYSTEM_PROMPT,
    PUBLISH_FORMATTER_API_CONTEXT,
    REVIEW_SYSTEM_PROMPT,
    _chat_completion_body,
    _extract_message_content,
    complete_issue_comment_markdown,
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
        mock_settings.revy_moonshot_max_completion_tokens = 32768
        mock_settings.revy_revision_llm_http_timeout_seconds.return_value = 60.0
        content = await complete_review(client, profile="standard", user_prompt="review")

    assert json.loads(content)["findings"] == []
    post_kwargs = client.post.call_args.kwargs
    body = post_kwargs["json"]
    assert body["model"] == "kimi-k2.7-code"
    assert body["response_format"] == {"type": "json_object"}
    assert "temperature" not in body
    assert "thinking" not in body
    assert body["max_completion_tokens"] == 32768


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


def test_parse_review_json_rejects_non_list_findings():
    with pytest.raises(ValueError, match="review_json_findings_not_list"):
        parse_review_json(json.dumps({"findings": {"title": "x"}}))


def test_parse_review_json_strips_markdown_fence():
    raw = """```json
{"findings": [{"title": "x", "severity": "info", "category": "other", "message": "m"}]}
```"""
    findings = parse_review_json(raw)
    assert len(findings) == 1
    assert findings[0]["title"] == "x"


def test_chat_completion_body_k2_7_code_omits_temperature():
    body = _chat_completion_body(
        model="kimi-k2.7-code",
        profile="standard",
        messages=[{"role": "user", "content": "x"}],
    )
    assert "temperature" not in body
    assert "thinking" not in body
    assert body["max_completion_tokens"] == 32768
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


def test_review_system_prompt_appends_publish_formatter_api_block():
    assert REVIEW_SYSTEM_PROMPT.endswith(PUBLISH_FORMATTER_API_CONTEXT)
    assert (
        "format_summary_comment(*, generation_groups, pr_active_groups)"
        in PUBLISH_FORMATTER_API_CONTEXT
    )
    assert "valid parameter names, not typos" in PUBLISH_FORMATTER_API_CONTEXT


def test_issue_comment_format_system_prompt_lists_required_sections():
    prompt = ISSUE_COMMENT_FORMAT_SYSTEM_PROMPT.lower()
    assert "short narrative" not in prompt
    assert "rationale" in prompt
    assert "merge recommendation" in prompt
    assert "this generation" in prompt
    assert "still open on pr" in prompt
    assert "pr summary" in prompt
    assert "heading stub only" in prompt
    assert "deterministic post-process" in prompt
    assert "security review" in prompt
    assert "important files changed" in prompt


@pytest.mark.asyncio
async def test_complete_issue_comment_markdown_uses_issue_comment_system_prompt():
    payload = {
        "choices": [{"message": {"content": "## Revy code review\n\n**Confidence score:** 4/5"}}],
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
        mock_settings.revy_moonshot_max_completion_tokens = 32768
        mock_settings.revy_revision_llm_http_timeout_seconds.return_value = 60.0
        await complete_issue_comment_markdown(
            client,
            profile="standard",
            user_prompt="format this",
        )

    body = client.post.call_args.kwargs["json"]
    messages = body["messages"]
    assert messages[0]["role"] == "system"
    assert messages[0]["content"] == ISSUE_COMMENT_FORMAT_SYSTEM_PROMPT


@pytest.mark.asyncio
async def test_complete_issue_comment_markdown_returns_markdown_without_json_format():
    payload = {
        "choices": [{"message": {"content": "## Revy code review\n\n**Confidence score:** 4/5"}}],
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
        mock_settings.revy_moonshot_max_completion_tokens = 32768
        mock_settings.revy_revision_llm_http_timeout_seconds.return_value = 60.0
        content = await complete_issue_comment_markdown(
            client,
            profile="standard",
            user_prompt="format this",
        )

    assert content.startswith("## Revy code review")
    body = client.post.call_args.kwargs["json"]
    assert "response_format" not in body


def test_chat_completion_body_json_response_false_omits_response_format():
    body = _chat_completion_body(
        model="moonshot-v1-8k",
        profile="standard",
        messages=[{"role": "user", "content": "x"}],
        json_response=False,
    )
    assert "response_format" not in body
    assert body["temperature"] == 0.2
