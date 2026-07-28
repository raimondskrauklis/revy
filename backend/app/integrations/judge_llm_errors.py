# backend/app/integrations/judge_llm_errors.py
"""Judge LLM parse errors — shared by Anthropic and Bedrock paths."""
from __future__ import annotations

import json

JUDGE_RESPONSE_TEXT_MAX_BYTES = 512 * 1024


class JudgeParseError(ValueError):
    """HTTP 200 body could not be parsed as judge JSON."""

    def __init__(self, code: str, *, response_text: str) -> None:
        super().__init__(code)
        self.code = code
        self.response_text = truncate_judge_response_text(response_text)


def truncate_judge_response_text(text: str) -> str:
    encoded = text.encode("utf-8")
    if len(encoded) <= JUDGE_RESPONSE_TEXT_MAX_BYTES:
        return text
    return encoded[:JUDGE_RESPONSE_TEXT_MAX_BYTES].decode("utf-8", errors="ignore")


def parse_judge_payload(text: str) -> dict:
    try:
        payload = json.loads(text)
    except json.JSONDecodeError as exc:
        raise JudgeParseError("judge_json_invalid", response_text=text) from exc
    if not isinstance(payload, dict):
        raise JudgeParseError("judge_json_not_object", response_text=text)
    return payload


def judge_failure_trace_fields(
    exc: Exception,
) -> tuple[str | None, str | None, int | None]:
    """Returns (raw_response_text, parse_error, response_chars) for manifest + logs."""
    if isinstance(exc, JudgeParseError):
        return exc.response_text, exc.code, len(exc.response_text)
    return None, str(exc), None
