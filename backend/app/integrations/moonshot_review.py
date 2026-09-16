# backend/app/integrations/moonshot_review.py
"""Moonshot Kimi review client — R4 (OpenAI-compatible chat completions)."""
from __future__ import annotations

import time

import httpx

from app.constants.enums import GitHubReviewRunFailureClass
from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError
from app.core.logging import get_logger
from app.integrations.judge_llm_errors import parse_llm_json_object
from app.services.llm_call_recorder import (
    LlmAttemptCompleteContext,
    LlmAttemptFailContext,
    LlmAttemptStartContext,
    try_complete_attempt,
    try_fail_attempt,
    try_start_attempt,
)
from app.services.observability_failure import classify_failure_class

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
    "(5) ### PR summary (lifetime) — heading stub only; do not render scan table, bullets, or <details> "
    "(deterministic post-process replaces the full lifetime block); "
    "(6) **Since last push:** resolution prose when provided; "
    "(7) ### Files needing attention bullet list; "
    "(8) ### This generation markdown heading with severity table (Severity | Category | Title | File — no message column); "
    "(9) ### Still open on PR markdown heading with severity table (same columns — PR-wide active findings); "
    "(10) <details><summary>Security review</summary>…</details> when security findings exist; "
    "(11) <details><summary>Important files changed</summary> table (File | Note)…</details>; "
    "(12) <details><summary>Review metadata</summary> with head_sha and revision…</details>. "
    "Use the provided confidence value and rationale hints. Do not use mermaid. "
    "Keep under 12000 characters."
)

_K2_THINKING_MODEL_PREFIXES = (
    "kimi-k2.7-code",
    "kimi-k2.6",
    "kimi-k2.5",
)


def _normalized_model_id(model_id: str) -> str:
    return model_id.strip()


def _model_basename(model: str) -> str:
    return model.strip().lower().rsplit("/", 1)[-1]


def _uses_k2_thinking_params(model: str) -> bool:
    basename = _model_basename(model)
    return any(basename.startswith(prefix) for prefix in _K2_THINKING_MODEL_PREFIXES)


def _uses_k3_params(model: str) -> bool:
    return _model_basename(model).startswith("kimi-k3")


def _reasoning_effort_for_profile(profile: str) -> str:
    normalized = (profile or "standard").strip().lower()
    if normalized == "critical":
        return "max"
    if normalized == "deep":
        return "high"
    return "high"


def _max_completion_tokens() -> int:
    return settings.revy_moonshot_max_completion_tokens


def _chat_completions_url() -> str:
    configured = getattr(settings, "moonshot_chat_completions_url", None)
    if isinstance(configured, str) and configured.strip():
        return configured.strip()
    return MOONSHOT_API_URL


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
        # K3 API default max_completion_tokens is 131072 when omitted — do not cap lower.
        body["reasoning_effort"] = _reasoning_effort_for_profile(profile)
        return body
    if _uses_k2_thinking_params(model):
        # K2 thinking: reasoning_content + content share budget; API default ~1024 when omitted.
        body["max_completion_tokens"] = _max_completion_tokens()
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
    reasoning_content = message.get("reasoning_content")
    reasoning_chars = len(reasoning_content) if isinstance(reasoning_content, str) else 0
    logger.error(
        "moonshot_review_empty_content",
        extra={
            "model": model,
            "finish_reason": finish_reason,
            "has_reasoning_content": bool(reasoning_content),
            "reasoning_content_chars": reasoning_chars,
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
    recorder: LlmAttemptStartContext | None = None,
    api_url: str | None = None,
    api_key: str | None = None,
) -> str:
    key = (api_key or settings.moonshot_api_key or "").strip()
    if not key:
        raise ServiceUnavailableError(
            message="LLM API is not configured",
            error_code="llm_disabled",
        )

    if model_id and model_id.strip():
        resolved_model = model_id
    elif api_url:
        resolved_model = settings.revy_rtu_model_for_profile(profile)
    else:
        resolved_model = settings.revy_moonshot_model_for_profile(profile)
    model = _normalized_model_id(resolved_model)
    url = (api_url or "").strip() or _chat_completions_url()
    messages = [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
    ]
    attempt_id = None
    attempt_started = time.monotonic()
    if recorder is not None:
        attempt_id = await try_start_attempt(recorder)
    try:
        response = await client.post(
            url,
            headers={
                "Authorization": f"Bearer {key}",
                "Content-Type": "application/json",
            },
            json=_chat_completion_body(
                model=model,
                profile=profile,
                messages=messages,
                json_response=json_response,
            ),
            timeout=timeout_seconds
            or settings.revy_revision_llm_http_timeout_seconds(profile),
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
        content = _extract_message_content(first, model=model)
        if attempt_id is not None:
            usage = data.get("usage") if isinstance(data.get("usage"), dict) else {}
            await try_complete_attempt(
                attempt_id,
                context=LlmAttemptCompleteContext(
                    input_tokens=usage.get("prompt_tokens")
                    if isinstance(usage.get("prompt_tokens"), int)
                    else None,
                    output_tokens=usage.get("completion_tokens")
                    if isinstance(usage.get("completion_tokens"), int)
                    else None,
                    finish_reason=first.get("finish_reason")
                    if isinstance(first.get("finish_reason"), str)
                    else None,
                    wait_ms=int((time.monotonic() - attempt_started) * 1000),
                    http_status=response.status_code,
                    response_text=content,
                ),
            )
        return content
    except httpx.TimeoutException as exc:
        if attempt_id is not None:
            await try_fail_attempt(
                attempt_id,
                context=LlmAttemptFailContext(
                    failure_class=GitHubReviewRunFailureClass.timeout,
                    wait_ms=int((time.monotonic() - attempt_started) * 1000),
                ),
                exc=exc,
            )
        raise
    except httpx.HTTPError as exc:
        if attempt_id is not None:
            http_status = (
                exc.response.status_code
                if isinstance(exc, httpx.HTTPStatusError) and exc.response is not None
                else None
            )
            await try_fail_attempt(
                attempt_id,
                context=LlmAttemptFailContext(
                    failure_class=classify_failure_class(exc),
                    wait_ms=int((time.monotonic() - attempt_started) * 1000),
                    http_status=http_status,
                ),
                exc=exc,
            )
        raise
    except ServiceUnavailableError as exc:
        if attempt_id is not None:
            await try_fail_attempt(
                attempt_id,
                context=LlmAttemptFailContext(
                    failure_class=GitHubReviewRunFailureClass.parse_error,
                    wait_ms=int((time.monotonic() - attempt_started) * 1000),
                ),
                exc=exc,
            )
        raise
    except ValueError as exc:
        if attempt_id is not None:
            await try_fail_attempt(
                attempt_id,
                context=LlmAttemptFailContext(
                    failure_class=GitHubReviewRunFailureClass.parse_error,
                    wait_ms=int((time.monotonic() - attempt_started) * 1000),
                ),
                exc=exc,
            )
        raise
    except OSError as exc:
        if attempt_id is not None:
            await try_fail_attempt(
                attempt_id,
                context=LlmAttemptFailContext(
                    failure_class=classify_failure_class(exc),
                    wait_ms=int((time.monotonic() - attempt_started) * 1000),
                ),
                exc=exc,
            )
        raise


async def complete_review(
    client: httpx.AsyncClient,
    *,
    profile: str,
    user_prompt: str,
    model_id: str | None = None,
    timeout_seconds: float | None = None,
    api_url: str | None = None,
    api_key: str | None = None,
) -> str:
    return await _complete_chat(
        client,
        profile=profile,
        system_prompt=REVIEW_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        model_id=model_id,
        timeout_seconds=timeout_seconds,
        json_response=True,
        api_url=api_url,
        api_key=api_key,
    )


async def complete_issue_comment_markdown(
    client: httpx.AsyncClient,
    *,
    profile: str,
    user_prompt: str,
    model_id: str | None = None,
    timeout_seconds: float | None = None,
    recorder: LlmAttemptStartContext | None = None,
    api_url: str | None = None,
    api_key: str | None = None,
) -> str:
    """OpenAI-compatible chat completion for Greptile-shaped PR issue comments — markdown only."""
    return await _complete_chat(
        client,
        profile=profile,
        system_prompt=ISSUE_COMMENT_FORMAT_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        model_id=model_id,
        timeout_seconds=timeout_seconds,
        json_response=False,
        recorder=recorder,
        api_url=api_url,
        api_key=api_key,
    )


def parse_review_json(raw: str) -> list[dict]:
    """Parse LLM JSON payload — raises ValueError on invalid shape."""
    payload = parse_llm_json_object(raw)
    if not isinstance(payload, dict):
        raise ValueError("review_json_not_object")
    findings = payload.get("findings")
    if findings is None:
        return []
    if not isinstance(findings, list):
        raise ValueError("review_json_findings_not_list")
    return [item for item in findings if isinstance(item, dict)]
