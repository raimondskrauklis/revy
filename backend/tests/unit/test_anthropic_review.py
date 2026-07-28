# backend/tests/unit/test_anthropic_review.py
"""Anthropic review client — R4 scaffold."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core.exceptions import ServiceUnavailableError
from app.integrations import anthropic_review
from app.integrations.anthropic_review import complete_review, parse_review_json


@pytest.mark.asyncio
async def test_complete_review_disabled_raises():
    client = AsyncMock(spec=httpx.AsyncClient)
    with patch("app.integrations.anthropic_review.settings") as mock_settings:
        mock_settings.anthropic_api_key = None
        with pytest.raises(ServiceUnavailableError) as exc:
            await complete_review(client, user_prompt="review this")
    assert exc.value.error_code == "llm_disabled"


@pytest.mark.asyncio
async def test_judge_finding_falls_back_to_direct_when_gateway_fails():
    gateway_response = MagicMock()
    gateway_response.raise_for_status = MagicMock(side_effect=httpx.HTTPStatusError(
        "gateway down",
        request=MagicMock(),
        response=MagicMock(status_code=503),
    ))
    direct_response = MagicMock()
    direct_response.raise_for_status = MagicMock()
    direct_response.json.return_value = {
        "content": [{"text": json.dumps({"outcome": "upheld", "notes": "ok"})}]
    }
    client = AsyncMock(spec=httpx.AsyncClient)
    client.post = AsyncMock(side_effect=[gateway_response, direct_response])

    with patch("app.integrations.anthropic_review.settings") as mock_settings:
        mock_settings.anthropic_gateway_enabled = True
        mock_settings.anthropic_gateway_messages_url = "https://llm.ai.rtu.lv/v1/messages"
        mock_settings.anthropic_auth_token = "rtu-token"
        mock_settings.effective_anthropic_gateway_judge_model = "azure_ai/claude-opus-5"
        mock_settings.anthropic_direct_enabled = True
        mock_settings.anthropic_api_key = "direct-key"
        mock_settings.revy_anthropic_model = "claude-sonnet-5"
        mock_settings.revy_revision_timeout_standard_seconds = 30
        result = await anthropic_review.judge_finding(client, user_prompt="judge this")

    assert result["outcome"] == "upheld"
    assert client.post.await_count == 2
    gateway_call = client.post.await_args_list[0]
    direct_call = client.post.await_args_list[1]
    assert gateway_call.args[0] == "https://llm.ai.rtu.lv/v1/messages"
    assert "Bearer" in gateway_call.kwargs["headers"]["Authorization"]
    assert direct_call.args[0] == anthropic_review.ANTHROPIC_DIRECT_MESSAGES_URL
    assert direct_call.kwargs["headers"]["x-api-key"] == "direct-key"


@pytest.mark.asyncio
async def test_complete_review_returns_content():
    payload = {"content": [{"text": json.dumps({"findings": []})}]}
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = payload
    client = AsyncMock(spec=httpx.AsyncClient)
    client.post = AsyncMock(return_value=response)

    with patch("app.integrations.anthropic_review.settings") as mock_settings:
        mock_settings.anthropic_direct_enabled = True
        mock_settings.anthropic_api_key = "test-key"
        mock_settings.revy_anthropic_model = "claude-sonnet-5"
        mock_settings.revy_revision_timeout_standard_seconds = 30
        content = await complete_review(client, user_prompt="review")

    assert json.loads(content)["findings"] == []


def test_parse_review_json_empty_findings():
    assert parse_review_json(json.dumps({"findings": []})) == []


def test_build_verification_judge_prompt_includes_push_delta():
    from app.integrations.anthropic_review import (
        VERIFICATION_JUDGE_SYSTEM_PROMPT,
        build_verification_judge_prompt,
    )

    group = type(
        "Group",
        (),
        {
            "title": "Null deref",
            "severity": "error",
            "category": "bug",
            "file_path": "app/x.py",
            "message": "Possible null",
        },
    )()
    prompt = build_verification_judge_prompt(
        group=group,
        push_delta_patch="@@ -1 +1 @@\n-old\n+new\n",
        evidence_snippet="old line",
        start_line=10,
        end_line=10,
    )
    assert "push delta" in prompt.lower() or "Push delta" in prompt
    assert "Null deref" in prompt
    assert "@@ -1 +1 @@" not in prompt
    assert "old line" in prompt
    assert "upheld|dismissed" in VERIFICATION_JUDGE_SYSTEM_PROMPT


def test_build_verification_judge_prompt_includes_patch_without_snippet():
    from app.integrations.anthropic_review import build_verification_judge_prompt

    group = type(
        "Group",
        (),
        {
            "title": "Bug",
            "severity": "error",
            "category": "bug",
            "file_path": "app/x.py",
            "message": "msg",
        },
    )()
    prompt = build_verification_judge_prompt(
        group=group,
        push_delta_patch="@@ -1 +1 @@\n-old\n+new\n",
        evidence_snippet=None,
    )
    assert "@@ -1 +1 @@" in prompt


def test_build_verification_judge_prompt_whitespace_only_snippet_omits_evidence():
    from app.integrations.anthropic_review import build_verification_judge_prompt

    group = type(
        "Group",
        (),
        {
            "title": "Bug",
            "severity": "error",
            "category": "bug",
            "file_path": "app/x.py",
            "message": "msg",
        },
    )()
    prompt = build_verification_judge_prompt(
        group=group,
        push_delta_patch="@@ -1 +1 @@\n-old\n+new\n",
        evidence_snippet="   ",
    )
    assert "Evidence excerpt:" not in prompt
    assert "Push delta" in prompt


def test_judge_outcome_json_schema_matches_parse_judge_outcome():
    schema = anthropic_review.judge_outcome_json_schema()
    assert schema["required"] == ["outcome"]
    outcome_enum = schema["properties"]["outcome"]["enum"]
    for value in ("upheld", "dismissed", "modified"):
        outcome, notes = anthropic_review.parse_judge_outcome(
            {"outcome": value, "notes": "ok"}
        )
        assert outcome == value
        assert notes == "ok"
        assert value in outcome_enum


@pytest.mark.asyncio
async def test_post_structured_judge_smoke_sends_output_config():
    payload = {"content": [{"text": json.dumps({"outcome": "dismissed", "notes": "n/a"})}]}
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = payload
    client = AsyncMock(spec=httpx.AsyncClient)
    client.post = AsyncMock(return_value=response)

    with patch("app.integrations.anthropic_review.settings") as mock_settings:
        mock_settings.anthropic_gateway_messages_url = "https://llm.ai.rtu.lv/v1/messages"
        mock_settings.anthropic_auth_token = "rtu-token"
        mock_settings.effective_anthropic_gateway_judge_model = "azure_ai/claude-opus-5"
        mock_settings.revy_revision_timeout_standard_seconds = 30
        profile = anthropic_review._gateway_profile("claude-sonnet-5")
        assert profile is not None
        text = await anthropic_review._post_structured_judge_smoke(
            client,
            profile,
            user_prompt="judge this",
        )

    assert json.loads(text)["outcome"] == "dismissed"
    body = client.post.await_args.kwargs["json"]
    assert body["output_config"]["format"]["type"] == "json_schema"
    assert body["output_config"]["format"]["schema"]["required"] == ["outcome"]


def test_parse_judge_payload_invalid_json_raises_judge_parse_error():
    from app.integrations.judge_llm_errors import JudgeParseError, parse_judge_payload

    with pytest.raises(JudgeParseError) as exc_info:
        parse_judge_payload("not-json {")
    assert exc_info.value.code == "judge_json_invalid"
    assert "not-json" in exc_info.value.response_text


def test_parse_llm_json_object_strips_json_fence():
    from app.integrations.judge_llm_errors import parse_llm_json_object

    payload = parse_llm_json_object('```json\n{"outcome":"dismissed","notes":"ok"}\n```')
    assert payload["outcome"] == "dismissed"


def test_parse_llm_json_object_extracts_object_after_prose():
    from app.integrations.judge_llm_errors import parse_llm_json_object

    payload = parse_llm_json_object(
        'Here is the result:\n{"outcome":"upheld","notes":"supported"}'
    )
    assert payload["outcome"] == "upheld"


@pytest.mark.asyncio
async def test_judge_finding_parses_fenced_json_body():
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {
        "content": [{"text": '```json\n{"outcome":"dismissed","notes":"ok"}\n```'}]
    }
    client = AsyncMock(spec=httpx.AsyncClient)
    client.post = AsyncMock(return_value=response)

    with patch("app.integrations.anthropic_review.settings") as mock_settings:
        mock_settings.anthropic_gateway_enabled = True
        mock_settings.anthropic_gateway_messages_url = "https://llm.ai.rtu.lv/v1/messages"
        mock_settings.anthropic_auth_token = "rtu-token"
        mock_settings.effective_anthropic_gateway_judge_model = "azure_ai/claude-opus-5"
        mock_settings.anthropic_direct_enabled = False
        mock_settings.revy_judge_structured_output = False
        mock_settings.revy_revision_timeout_standard_seconds = 30
        result = await anthropic_review.judge_finding(client, user_prompt="judge this")

    assert result["outcome"] == "dismissed"


@pytest.mark.asyncio
async def test_judge_finding_structured_output_falls_back_on_400():
    structured_response = MagicMock()
    structured_response.status_code = 400
    structured_response.text = "structured_outputs not supported in your workspace"
    structured_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "bad request",
        request=MagicMock(),
        response=structured_response,
    )
    plain_response = MagicMock()
    plain_response.raise_for_status = MagicMock()
    plain_response.json.return_value = {
        "content": [{"text": json.dumps({"outcome": "upheld", "notes": "ok"})}]
    }
    client = AsyncMock(spec=httpx.AsyncClient)
    client.post = AsyncMock(side_effect=[structured_response, plain_response])

    with (
        patch("app.integrations.anthropic_review.settings") as mock_settings,
        patch(
            "app.integrations.anthropic_review._profile_supports_structured_output",
            return_value=True,
        ),
    ):
        mock_settings.anthropic_gateway_enabled = False
        mock_settings.anthropic_direct_enabled = True
        mock_settings.anthropic_api_key = "direct-key"
        mock_settings.revy_anthropic_model = "claude-sonnet-5"
        mock_settings.revy_judge_structured_output = True
        mock_settings.revy_revision_timeout_standard_seconds = 30
        result = await anthropic_review.judge_finding(client, user_prompt="judge this")

    assert result["outcome"] == "upheld"
    assert client.post.await_count == 2
    assert "output_config" in client.post.await_args_list[0].kwargs["json"]
    assert "output_config" not in client.post.await_args_list[1].kwargs["json"]


@pytest.mark.asyncio
async def test_judge_finding_structured_output_does_not_fallback_on_unrelated_400():
    bad_response = MagicMock()
    bad_response.status_code = 400
    bad_response.text = "invalid model id"
    bad_response.raise_for_status.side_effect = httpx.HTTPStatusError(
        "bad request",
        request=MagicMock(),
        response=bad_response,
    )
    client = AsyncMock(spec=httpx.AsyncClient)
    client.post = AsyncMock(return_value=bad_response)
    direct_profile = anthropic_review._AnthropicProfile(
        messages_url=anthropic_review.ANTHROPIC_DIRECT_MESSAGES_URL,
        auth_headers={"x-api-key": "direct-key"},
        model_id="claude-sonnet-5",
        label="direct",
    )

    with (
        patch("app.integrations.anthropic_review.settings") as mock_settings,
        patch(
            "app.integrations.anthropic_review._judge_profiles",
            return_value=[direct_profile],
        ),
        patch(
            "app.integrations.anthropic_review._profile_supports_structured_output",
            return_value=True,
        ),
        pytest.raises(httpx.HTTPStatusError),
    ):
        mock_settings.revy_judge_structured_output = True
        mock_settings.revy_revision_timeout_standard_seconds = 30
        await anthropic_review.judge_finding(client, user_prompt="judge this")

    assert client.post.await_count == 1


@pytest.mark.asyncio
async def test_judge_finding_raises_judge_parse_error_on_invalid_json():
    from app.integrations.judge_llm_errors import JudgeParseError

    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {"content": [{"text": "```not valid json```"}]}
    client = AsyncMock(spec=httpx.AsyncClient)
    client.post = AsyncMock(return_value=response)

    with patch("app.integrations.anthropic_review.settings") as mock_settings:
        mock_settings.anthropic_gateway_enabled = True
        mock_settings.anthropic_gateway_messages_url = "https://llm.ai.rtu.lv/v1/messages"
        mock_settings.anthropic_auth_token = "rtu-token"
        mock_settings.effective_anthropic_gateway_judge_model = "azure_ai/claude-opus-5"
        mock_settings.anthropic_direct_enabled = False
        mock_settings.revy_judge_structured_output = False
        mock_settings.revy_revision_timeout_standard_seconds = 30
        with pytest.raises(JudgeParseError) as exc_info:
            await anthropic_review.judge_finding(client, user_prompt="judge this")

    assert exc_info.value.code == "judge_json_invalid"
    assert "```not valid json```" in exc_info.value.response_text
