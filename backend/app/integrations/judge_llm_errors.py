# backend/app/integrations/judge_llm_errors.py
"""Judge LLM parse errors — shared by Anthropic and Bedrock paths."""
from __future__ import annotations

import json
import re

JUDGE_RESPONSE_TEXT_MAX_BYTES = 512 * 1024
_JSON_FENCE_RE = re.compile(r"^```(?:json)?\s*\n?(.*?)\n?```\s*$", re.DOTALL | re.IGNORECASE)


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


def _extract_json_object_text(text: str) -> str:
    stripped = text.strip()
    fence_match = _JSON_FENCE_RE.match(stripped)
    if fence_match is not None:
        stripped = fence_match.group(1).strip()
    start = stripped.find("{")
    if start < 0:
        raise ValueError("judge_json_invalid")
    end = stripped.rfind("}")
    if end < start:
        raise ValueError("judge_json_invalid")
    return stripped[start : end + 1]


def parse_llm_json_object(text: str) -> dict:
    """Strip fences / leading prose and parse the first JSON object."""
    try:
        payload = json.loads(_extract_json_object_text(text))
    except json.JSONDecodeError as exc:
        raise ValueError("judge_json_invalid") from exc
    if not isinstance(payload, dict):
        raise ValueError("judge_json_not_object")
    return payload


def parse_judge_payload(text: str) -> dict:
    try:
        return parse_llm_json_object(text)
    except ValueError as exc:
        raise JudgeParseError(str(exc), response_text=text) from exc


def judge_failure_trace_fields(
    exc: Exception,
) -> tuple[str | None, str | None, int | None]:
    """Returns (raw_response_text, parse_error, response_chars) for manifest + logs."""
    if isinstance(exc, JudgeParseError):
        return exc.response_text, exc.code, len(exc.response_text)
    return None, str(exc), None
