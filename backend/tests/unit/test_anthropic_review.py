# backend/tests/unit/test_anthropic_review.py
"""Anthropic review client — R4 scaffold."""
import json
from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from app.core.exceptions import ServiceUnavailableError
from app.integrations import anthropic_review
from app.integrations.anthropic_review import complete_review, parse_review_json
from app.integrations.judge_llm_errors import JudgeParseError

_RTU_MESSAGES_URL = "https://llm.ai.rtu.lv/v1/messages"


def _rtu_judge_kwargs(**extra):
    return {
        "messages_url": _RTU_MESSAGES_URL,
        "api_key": "rtu-key",
        "model_id": "azure_ai/claude-opus-5",
        **extra,
    }


@pytest.mark.asyncio
async def test_complete_review_disabled_raises():
    client = AsyncMock(spec=httpx.AsyncClient)
    with patch("app.integrations.anthropic_review.settings") as mock_settings:
        mock_settings.anthropic_api_key = None
        with pytest.raises(ServiceUnavailableError) as exc:
            await complete_review(client, user_prompt="review this")
    assert exc.value.error_code == "llm_disabled"


@pytest.mark.asyncio
async def test_judge_finding_rtu_uses_bearer_messages_url():
    payload = {
        "content": [{"text": json.dumps({"outcome": "upheld", "notes": "ok"})}]
    }
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = payload
    client = AsyncMock(spec=httpx.AsyncClient)
    client.post = AsyncMock(return_value=response)

    with patch("app.integrations.anthropic_review.settings") as mock_settings:
        mock_settings.revy_revision_timeout_standard_seconds = 30
        mock_settings.anthropic_api_key = "direct-key"
        result = await anthropic_review.judge_finding(
            client,
            user_prompt="judge this",
            **_rtu_judge_kwargs(),
        )

    assert result["outcome"] == "upheld"
    assert client.post.await_count == 1
    assert client.post.await_args.args[0] == _RTU_MESSAGES_URL
    assert client.post.await_args.kwargs["headers"]["Authorization"] == "Bearer rtu-key"


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


@pytest.mark.asyncio
async def test_complete_review_thinking_only_raises_service_unavailable():
    payload = {
        "content": [
            {"type": "thinking", "thinking": "", "signature": "sig-review"},
        ]
    }
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
        with pytest.raises(ServiceUnavailableError) as exc_info:
            await complete_review(client, user_prompt="review")

    assert exc_info.value.message == "Anthropic response invalid"
    assert exc_info.value.error_code == "llm_error"


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
        mock_settings.revy_judge_structured_output = False
        mock_settings.revy_revision_timeout_standard_seconds = 30
        result = await anthropic_review.judge_finding(
            client,
            user_prompt="judge this",
            **_rtu_judge_kwargs(),
        )

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
        mock_settings.revy_judge_structured_output = False
        mock_settings.revy_revision_timeout_standard_seconds = 30
        with pytest.raises(JudgeParseError) as exc_info:
            await anthropic_review.judge_finding(
                client,
                user_prompt="judge this",
                **_rtu_judge_kwargs(),
            )

    assert exc_info.value.code == "judge_json_invalid"
    assert "```not valid json```" in exc_info.value.response_text


@pytest.mark.asyncio
async def test_judge_finding_thinking_only_raises_judge_empty_text():
    from app.integrations.judge_llm_errors import JudgeParseError

    payload = {
        "content": [
            {"type": "thinking", "thinking": "", "signature": "sig-judge"},
        ],
        "usage": {"input_tokens": 3, "output_tokens": 1},
    }
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = payload
    client = AsyncMock(spec=httpx.AsyncClient)
    client.post = AsyncMock(return_value=response)

    with patch("app.integrations.anthropic_review.settings") as mock_settings:
        mock_settings.revy_judge_structured_output = False
        mock_settings.revy_revision_timeout_standard_seconds = 30
        with pytest.raises(JudgeParseError) as exc_info:
            await anthropic_review.judge_finding(
                client,
                user_prompt="judge this",
                **_rtu_judge_kwargs(),
            )

    assert exc_info.value.code == "judge_empty_text"
    transport = anthropic_review.get_judge_transport_log_fields()
    assert transport["parse_error"] == "judge_empty_text"
    assert transport["content_block_types"] == ["thinking"]
    assert "signature" not in transport


@pytest.mark.asyncio
async def test_judge_empty_text_info_logs_do_not_include_signature(caplog):
    payload = {
        "content": [
            {"type": "thinking", "thinking": "", "signature": "sig-must-not-log"},
        ]
    }
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = payload
    client = AsyncMock(spec=httpx.AsyncClient)
    client.post = AsyncMock(return_value=response)

    with patch("app.integrations.anthropic_review.settings") as mock_settings:
        mock_settings.revy_judge_structured_output = False
        mock_settings.revy_revision_timeout_standard_seconds = 30
        with caplog.at_level("INFO"):
            with pytest.raises(JudgeParseError):
                await anthropic_review.judge_finding(
                    client,
                    user_prompt="judge this",
                    **_rtu_judge_kwargs(),
                )

    for record in caplog.records:
        extra = getattr(record, "__dict__", {})
        assert extra.get("signature") is None
        assert "sig-must-not-log" not in record.getMessage()
        dumped = " ".join(f"{k}={v}" for k, v in extra.items() if k != "msg")
        assert "sig-must-not-log" not in dumped


def test_extract_usage_fields_reads_token_counts():
    fields = anthropic_review._extract_usage_fields(
        {"usage": {"input_tokens": 42, "output_tokens": 7}}
    )
    assert fields == {"input_tokens": 42, "output_tokens": 7}


def test_extract_usage_fields_empty_when_missing():
    assert anthropic_review._extract_usage_fields({}) == {}


def test_extract_message_text_empty_content_includes_preview():
    with pytest.raises(ServiceUnavailableError) as exc_info:
        anthropic_review._extract_message_text({"content": [], "id": "msg_empty"})
    assert exc_info.value.message == "Anthropic response invalid"
    preview = exc_info.value.details.get("response_body_preview")
    assert isinstance(preview, str)
    assert "msg_empty" in preview


def test_extract_message_text_legacy_content_zero_text():
    payload = {"content": [{"text": '{"outcome":"dismissed"}'}]}
    assert anthropic_review._extract_message_text(payload) == '{"outcome":"dismissed"}'


def test_extract_message_text_thinking_first_text_later():
    assistant = '{"outcome":"upheld","notes":"ok"}'
    payload = {
        "content": [
            {"type": "thinking", "thinking": "", "signature": "sig-live"},
            {"type": "text", "text": assistant},
        ]
    }
    assert anthropic_review._extract_message_text(payload) == assistant


def test_extract_message_text_thinking_only_returns_empty_string():
    payload = {
        "content": [
            {"type": "thinking", "thinking": "", "signature": "sig-only"},
        ]
    }
    assert anthropic_review._extract_message_text(payload) == ""


def test_extract_message_text_thinking_only_does_not_raise_judge_parse_error():
    payload = {
        "content": [
            {"type": "thinking", "thinking": "", "signature": "sig-only"},
        ]
    }
    try:
        result = anthropic_review._extract_message_text(payload)
    except JudgeParseError as exc:
        pytest.fail(f"helper raised JudgeParseError: {exc}")
    assert result == ""


def test_extract_message_text_concatenates_multiple_text_blocks():
    payload = {
        "content": [
            {"type": "thinking", "thinking": "hidden", "signature": "sig"},
            {"type": "text", "text": '{"outcome":'},
            {"type": "redacted_thinking", "data": "x"},
            {"type": "text", "text": '"upheld"}'},
        ]
    }
    assert anthropic_review._extract_message_text(payload) == '{"outcome":"upheld"}'


def test_extract_message_text_skips_non_dict_and_blank_text():
    payload = {
        "content": [
            "not-a-block",
            {"type": "text", "text": "   "},
            {"type": "text", "text": "kept"},
        ]
    }
    assert anthropic_review._extract_message_text(payload) == "kept"


def test_judge_raw_response_with_usage_attaches_transport_tokens():
    anthropic_review._set_judge_transport_context(
        {"input_tokens": 99, "output_tokens": 7}
    )
    raw = anthropic_review.judge_raw_response_with_usage(
        {"outcome": "dismissed", "notes": "ok"}
    )
    assert raw["usage"] == {"input_tokens": 99, "output_tokens": 7}
    in_tok, out_tok = anthropic_review.judge_token_usage_from_transport()
    assert in_tok == 99
    assert out_tok == 7


@pytest.mark.asyncio
async def test_judge_llm_request_started_and_completed_logged(caplog):
    payload = {
        "content": [{"text": json.dumps({"outcome": "dismissed", "notes": "ok"})}],
        "usage": {"input_tokens": 10, "output_tokens": 5},
    }
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = payload
    client = AsyncMock(spec=httpx.AsyncClient)
    client.post = AsyncMock(return_value=response)

    with patch("app.integrations.anthropic_review.settings") as mock_settings:
        mock_settings.anthropic_gateway_enabled = False
        mock_settings.anthropic_gateway_messages_url = None
        mock_settings.anthropic_auth_token = None
        mock_settings.anthropic_direct_enabled = True
        mock_settings.anthropic_api_key = "direct-key"
        mock_settings.revy_anthropic_model = "claude-sonnet-5"
        mock_settings.revy_judge_structured_output = False
        mock_settings.revy_revision_timeout_standard_seconds = 30
        with caplog.at_level("INFO"):
            await anthropic_review.judge_finding(client, user_prompt="judge this")

    messages = [record.message for record in caplog.records]
    assert "judge_llm_request_started" in messages
    assert "judge_llm_request_completed" in messages
    transport = anthropic_review.get_judge_transport_log_fields()
    assert transport["profile"] == "direct"
    assert transport["input_tokens"] == 10
    assert transport["output_tokens"] == 5
    assert transport["response_chars"] > 0


@pytest.mark.asyncio
async def test_parse_messages_response_json_preserves_body_preview():
    response = MagicMock()
    response.json.side_effect = json.JSONDecodeError("bad", "doc", 0)
    response.text = "<html>gateway error</html>"

    with pytest.raises(ServiceUnavailableError) as exc_info:
        anthropic_review._parse_messages_response_json(response)

    assert exc_info.value.details["response_body_preview"] == "<html>gateway error</html>"


@pytest.mark.asyncio
async def test_judge_transport_context_resets_between_calls():
    first_response = MagicMock()
    first_response.raise_for_status = MagicMock()
    first_response.json.return_value = {
        "content": [{"text": json.dumps({"outcome": "dismissed", "notes": "ok"})}]
    }
    client = AsyncMock(spec=httpx.AsyncClient)
    client.post = AsyncMock(return_value=first_response)

    with patch("app.integrations.anthropic_review.settings") as mock_settings:
        mock_settings.anthropic_gateway_enabled = False
        mock_settings.anthropic_gateway_messages_url = None
        mock_settings.anthropic_auth_token = None
        mock_settings.anthropic_direct_enabled = True
        mock_settings.anthropic_api_key = "direct-key"
        mock_settings.revy_anthropic_model = "claude-sonnet-5"
        mock_settings.revy_judge_structured_output = False
        mock_settings.revy_revision_timeout_standard_seconds = 30
        await anthropic_review.judge_finding(client, user_prompt="first")
        assert anthropic_review.get_judge_transport_log_fields().get("profile") == "direct"
        anthropic_review._set_judge_transport_context({"profile": "stale"})
        await anthropic_review.judge_finding(client, user_prompt="second")

    assert anthropic_review.get_judge_transport_log_fields().get("profile") == "direct"
    assert "stale" not in anthropic_review.get_judge_transport_log_fields().values()


@pytest.mark.asyncio
async def test_judge_transport_records_http_error_type_on_failure():
    response = MagicMock()
    response.raise_for_status = MagicMock(
        side_effect=httpx.HTTPStatusError(
            "bad gateway",
            request=MagicMock(),
            response=MagicMock(status_code=502),
        )
    )
    client = AsyncMock(spec=httpx.AsyncClient)
    client.post = AsyncMock(return_value=response)
    profile = anthropic_review._AnthropicProfile(
        messages_url="https://llm.ai.rtu.lv/v1/messages",
        auth_headers={"Authorization": "Bearer token"},
        model_id="claude-sonnet-5",
        label="gateway",
        allow_judge_profile_fallback=True,
    )

    anthropic_review._set_judge_transport_context({})
    with pytest.raises(httpx.HTTPStatusError):
        await anthropic_review._post_judge_anthropic_messages(
            client,
            profile,
            system="sys",
            user_prompt="judge",
            max_tokens=1024,
            timeout_seconds=30.0,
        )

    transport = anthropic_review.get_judge_transport_log_fields()
    assert transport["profile"] == "gateway"
    assert transport["error_type"] == "HTTPStatusError"
    assert "parse_error" in transport


@pytest.mark.asyncio
async def test_judge_transport_does_not_record_context_on_unexpected_error():
    response = MagicMock()
    response.raise_for_status = MagicMock()
    response.json.return_value = {"content": [{"text": "ok"}]}
    client = AsyncMock(spec=httpx.AsyncClient)
    client.post = AsyncMock(return_value=response)
    profile = anthropic_review._AnthropicProfile(
        messages_url=anthropic_review.ANTHROPIC_DIRECT_MESSAGES_URL,
        auth_headers={"x-api-key": "key"},
        model_id="claude-sonnet-5",
        label="direct",
    )

    anthropic_review._set_judge_transport_context({})
    with (
        patch(
            "app.integrations.anthropic_review._extract_message_text",
            side_effect=RuntimeError("programming error"),
        ),
        pytest.raises(RuntimeError, match="programming error"),
    ):
        await anthropic_review._post_judge_anthropic_messages(
            client,
            profile,
            system="sys",
            user_prompt="judge",
            max_tokens=1024,
            timeout_seconds=30.0,
        )

    assert anthropic_review.get_judge_transport_log_fields() == {}
