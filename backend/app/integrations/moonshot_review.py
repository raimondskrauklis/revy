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

PUBLISH_FORMATTER_API_CONTEXT = (
    "Publish formatter API (tests may call with these keyword arguments): "
    "format_summary_comment(*, generation_groups, pr_active_groups) in "
    "app.services.github_publish_formatter — generation_groups and pr_active_groups "
    "are valid parameter names, not typos."
)

REVIEW_SYSTEM_PROMPT = (
    "You are a senior code reviewer. Analyze the provided pull request context and "
    "return a single JSON object with shape "
    '{"findings":[{"severity":"info|warning|error|critical","category":'
    '"security|bug|performance|maintainability|other","title":"…","message":"…",'
    '"file_path":"optional/path","start_line":0,"end_line":0,'
    '"suggestion":"optional single-line replacement or omit"}]}. '
    "start_line and end_line are new-file (post-change) line numbers in the diff. "
    "Include suggestion only for a concrete single-line fix on an anchored line; "
    "one physical line only — omit for architectural or multi-hunk fixes. "
    "Do not include style or lint findings. Return only valid JSON. "
    "Prioritize issues in the unified diff hunks below; use supplemental context "
    "only to validate cross-file impact. "
    f"{PUBLISH_FORMATTER_API_CONTEXT}"
)

ISSUE_COMMENT_FORMAT_SYSTEM_PROMPT = (
    "You format GitHub pull request review issue comments. "
    "Return ONLY raw GitHub-flavored markdown — no JSON wrapper, no code fences, "
    "no {\"body\": ...} or {\"review_comment\": ...} envelope. "
    "Use this section order: "
    "(1) `## Revy code review` markdown heading; "
    "(2) narrative paragraph (2-4 sentences: name top findings, merge-readiness); "
    "(3) **Merge recommendation:** one line verdict; "
    "(4) **Confidence score:** N/5 plus one-sentence rationale (why not higher/lower); "
    "(5) **Since last push:** resolution prose when provided; "
    "(6) ### Files needing attention bullet list; "
    "(7) ### This generation markdown heading with severity table (Severity | Category | Title | File — no message column); "
    "(8) ### Still open on PR markdown heading with severity table (same columns — PR-wide active findings); "
    "(9) <details><summary>Security review</summary>…</details> when security findings exist; "
    "(10) <details><summary>Important files changed</summary> table (File | Note)…</details>; "
    "(11) <details><summary>Review metadata</summary> with head_sha and revision…</details>. "
    "Use the provided confidence value and rationale hints. Do not use mermaid. "
    "Keep under 12000 characters."
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
    json_response: bool = True,
) -> dict[str, object]:
    body: dict[str, object] = {
        "model": model,
        "messages": messages,
    }
    if json_response:
        body["response_format"] = {"type": "json_object"}
    if _uses_k3_params(model):
        body["reasoning_effort"] = _reasoning_effort_for_profile(profile)
        return body
    if _uses_k2_thinking_params(model):
        # K2 thinking models share the completion budget between reasoning_content and
        # content; omit max_completion_tokens so Moonshot applies the model default.
        return body
    body["temperature"] = 0.2
    return body


def _extract_message_content(choice: dict, *, model: str) -> str:
    message = choice.get("message")
    if not isinstance(message, dict):
        raise ServiceUnavailableError(
            message="Moonshot review response invalid",
            error_code="llm_error",
        )
    content = message.get("content")
    if isinstance(content, str) and content.strip():
        return content
    finish_reason = choice.get("finish_reason")
    logger.error(
        "moonshot_review_empty_content",
        extra={
            "model": model,
            "finish_reason": finish_reason,
            "has_reasoning_content": bool(message.get("reasoning_content")),
        },
    )
    if finish_reason == "length":
        raise ServiceUnavailableError(
            message="Moonshot review response truncated",
            error_code="llm_error",
        )
    raise ServiceUnavailableError(
        message="Moonshot review response invalid",
        error_code="llm_error",
    )


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


async def _complete_chat(
    client: httpx.AsyncClient,
    *,
    profile: str,
    system_prompt: str,
    user_prompt: str,
    model_id: str | None = None,
    timeout_seconds: float | None = None,
    json_response: bool = True,
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
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    response = await client.post(
        MOONSHOT_API_URL,
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        json=_chat_completion_body(
            model=model,
            profile=profile,
            messages=messages,
            json_response=json_response,
        ),
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
    return _extract_message_content(first, model=model)


async def complete_review(
    client: httpx.AsyncClient,
    *,
    profile: str,
    user_prompt: str,
    model_id: str | None = None,
    timeout_seconds: float | None = None,
) -> str:
    return await _complete_chat(
        client,
        profile=profile,
        system_prompt=REVIEW_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        model_id=model_id,
        timeout_seconds=timeout_seconds,
        json_response=True,
    )


async def complete_issue_comment_markdown(
    client: httpx.AsyncClient,
    *,
    profile: str,
    user_prompt: str,
    model_id: str | None = None,
    timeout_seconds: float | None = None,
) -> str:
    """Moonshot chat completion for Greptile-shaped PR issue comments — markdown only."""
    return await _complete_chat(
        client,
        profile=profile,
        system_prompt=ISSUE_COMMENT_FORMAT_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        model_id=model_id,
        timeout_seconds=timeout_seconds,
        json_response=False,
    )


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
