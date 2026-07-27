# backend/app/integrations/moonshot_review.py
"""Moonshot Kimi review client — R4 (OpenAI-compatible chat completions)."""
from __future__ import annotations

import json

import httpx

from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError
from app.core.logging import get_logger

logger = get_logger(__name__)

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

_K2_THINKING_MODEL_PREFIXES = (
    "kimi-k2.7-code",
    "kimi-k2.6",
    "kimi-k2.5",
)


def _require_moonshot_configured() -> None:
    if not settings.moonshot_api_key or not settings.moonshot_api_key.strip():
        raise ServiceUnavailableError(
            message="LLM API is not configured",
            error_code="llm_disabled",
        )


def _normalized_model_id(model_id: str) -> str:
    return model_id.strip()


def _uses_k2_thinking_params(model: str) -> bool:
    normalized = model.strip().lower()
    return any(normalized.startswith(prefix) for prefix in _K2_THINKING_MODEL_PREFIXES)


def _uses_k3_params(model: str) -> bool:
    return model.strip().lower().startswith("kimi-k3")


def _reasoning_effort_for_profile(profile: str) -> str:
    normalized = (profile or "standard").strip().lower()
    if normalized == "critical":
        return "max"
    if normalized == "deep":
        return "high"
    return "high"


def _chat_completion_body(
    *,
    model: str,
    profile: str,
    messages: list[dict[str, str]],
) -> dict[str, object]:
    body: dict[str, object] = {
        "model": model,
        "messages": messages,
        "response_format": {"type": "json_object"},
        "max_completion_tokens": settings.revy_moonshot_max_completion_tokens,
    }
    if _uses_k3_params(model):
        body["reasoning_effort"] = _reasoning_effort_for_profile(profile)
        return body
    if _uses_k2_thinking_params(model):
        # kimi-k2.7-code/k2.6/k2.5 reject non-default sampling params (temperature≠1.0 → 400).
        body["thinking"] = {"type": "enabled"}
        return body
    body["temperature"] = 0.2
    return body


def _log_moonshot_error(response: httpx.Response, *, model: str) -> None:
    if response.status_code < 400:
        return
    logger.error(
        "moonshot_review_request_failed",
        extra={
            "status_code": response.status_code,
            "model": model,
            "body": response.text[:2000],
        },
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

    model = _normalized_model_id(model_id or settings.revy_moonshot_model_for_profile(profile))
    messages = [
        {"role": "system", "content": REVIEW_SYSTEM_PROMPT},
        {"role": "user", "content": user_prompt},
    ]
    response = await client.post(
        MOONSHOT_API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=_chat_completion_body(model=model, profile=profile, messages=messages),
        timeout=timeout_seconds or settings.revy_revision_timeout_seconds(profile),
    )
    _log_moonshot_error(response, model=model)
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
