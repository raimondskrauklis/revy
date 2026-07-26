# backend/app/integrations/anthropic_review.py
"""Anthropic messages API client — R4 scaffold (R5 judge reuse)."""
from __future__ import annotations

import json

import httpx

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError

ANTHROPIC_API_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

REVIEW_SYSTEM_PROMPT = (
    "You are a senior code reviewer. Return a single JSON object with shape "
    '{"findings":[{"severity":"info|warning|error|critical","category":'
    '"security|bug|performance|maintainability|other","title":"…","message":"…",'
    '"file_path":"optional/path","start_line":0,"end_line":0}]}. '
    "Do not include style or lint findings. Return only valid JSON."
)


def _require_anthropic_enabled() -> None:
    if not settings.anthropic_api_key or not settings.anthropic_api_key.strip():
        raise ServiceUnavailableError(
            message="Anthropic API is not configured",
            error_code="llm_disabled",
        )


async def complete_review(
    client: httpx.AsyncClient,
    *,
    user_prompt: str,
    timeout_seconds: float | None = None,
) -> str:
    _require_anthropic_enabled()
    api_key = settings.anthropic_api_key
    if not api_key:
        raise ServiceUnavailableError(
            message="Anthropic API is not configured",
            error_code="llm_disabled",
        )

    response = await client.post(
        ANTHROPIC_API_URL,
        headers={
            "x-api-key": api_key,
            "anthropic-version": ANTHROPIC_VERSION,
            "Content-Type": "application/json",
        },
        json={
            "model": settings.revy_anthropic_model,
            "max_tokens": 4096,
            "system": REVIEW_SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_prompt}],
        },
        timeout=timeout_seconds or settings.revy_revision_timeout_standard_seconds,
    )
    response.raise_for_status()
    data = response.json()
    content_blocks = data.get("content")
    if not isinstance(content_blocks, list) or not content_blocks:
        raise ServiceUnavailableError(
            message="Anthropic review response invalid",
            error_code="llm_error",
        )
    first = content_blocks[0]
    if not isinstance(first, dict):
        raise ServiceUnavailableError(
            message="Anthropic review response invalid",
            error_code="llm_error",
        )
    text = first.get("text")
    if not isinstance(text, str) or not text.strip():
        raise ServiceUnavailableError(
            message="Anthropic review response invalid",
            error_code="llm_error",
        )
    return text


def parse_review_json(raw: str) -> list[dict]:
    """Parse LLM JSON payload — raises ValueError on invalid shape."""
    payload = json.loads(raw)
    if not isinstance(payload, dict):
        raise ValueError("review_json_not_object")
    findings = payload.get("findings")
    if findings is None:
        return []
    if not isinstance(findings, list):
        raise ValueError("review_json_findings_not_list")
    return [item for item in findings if isinstance(item, dict)]
