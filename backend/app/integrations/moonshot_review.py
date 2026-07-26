# backend/app/integrations/moonshot_review.py
"""Moonshot Kimi review client — R4 (OpenAI-compatible chat completions)."""
from __future__ import annotations

import json

import httpx

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError

MOONSHOT_API_URL = "https://api.moonshot.ai/v1/chat/completions"

REVIEW_SYSTEM_PROMPT = (
    "You are a senior code reviewer. Analyze the provided pull request context and "
    "return a single JSON object with shape "
    '{"findings":[{"severity":"info|warning|error|critical","category":'
    '"security|bug|performance|maintainability|other","title":"…","message":"…",'
    '"file_path":"optional/path","start_line":0,"end_line":0,'
    '"suggestion":"optional single-line replacement or omit"}]}. '
    "Include suggestion only for a concrete single-line fix on an anchored line; "
    "one physical line only — omit for architectural or multi-hunk fixes. "
    "Do not include style or lint findings. Return only valid JSON."
)


def _require_moonshot_configured() -> None:
    if not settings.moonshot_api_key or not settings.moonshot_api_key.strip():
        raise ServiceUnavailableError(
            message="LLM API is not configured",
            error_code="llm_disabled",
        )


async def complete_review(
    client: httpx.AsyncClient,
    *,
    profile: str,
    user_prompt: str,
    model_id: str | None = None,
    timeout_seconds: float | None = None,
) -> str:
    _require_moonshot_configured()
    api_key = settings.moonshot_api_key
    if not api_key:
        raise ServiceUnavailableError(
            message="LLM API is not configured",
            error_code="llm_disabled",
        )

    model = model_id or settings.revy_moonshot_model_for_profile(profile)
    response = await client.post(
        MOONSHOT_API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json={
            "model": model,
            "messages": [
                {"role": "system", "content": REVIEW_SYSTEM_PROMPT},
                {"role": "user", "content": user_prompt},
            ],
            "temperature": 0.2,
            "response_format": {"type": "json_object"},
        },
        timeout=timeout_seconds or settings.revy_revision_timeout_seconds(profile),
    )
    response.raise_for_status()
    data = response.json()
    choices = data.get("choices")
    if not isinstance(choices, list) or not choices:
        raise ServiceUnavailableError(
            message="Moonshot review response invalid",
            error_code="llm_error",
        )
    first = choices[0]
    if not isinstance(first, dict):
        raise ServiceUnavailableError(
            message="Moonshot review response invalid",
            error_code="llm_error",
        )
    message = first.get("message")
    if not isinstance(message, dict):
        raise ServiceUnavailableError(
            message="Moonshot review response invalid",
            error_code="llm_error",
        )
    content = message.get("content")
    if not isinstance(content, str) or not content.strip():
        raise ServiceUnavailableError(
            message="Moonshot review response invalid",
            error_code="llm_error",
        )
    return content


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
