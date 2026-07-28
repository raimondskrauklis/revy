# backend/app/integrations/anthropic_review.py
"""Anthropic messages API client — R4 scaffold (R5 judge reuse)."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass

import httpx

from app.constants.enums import stored_enum_value
from app.core.config import settings
from app.core.exceptions import ServiceUnavailableError
from app.integrations.judge_llm_errors import parse_judge_payload

ANTHROPIC_DIRECT_MESSAGES_URL = "https://api.anthropic.com/v1/messages"
ANTHROPIC_VERSION = "2023-06-01"

logger = logging.getLogger(__name__)

REVIEW_SYSTEM_PROMPT = (
    "You are a senior code reviewer. Return a single JSON object with shape "
    '{"findings":[{"severity":"info|warning|error|critical","category":'
    '"security|bug|performance|maintainability|other","title":"…","message":"…",'
    '"file_path":"optional/path","start_line":0,"end_line":0,'
    '"suggestion":"optional single-line replacement or omit"}]}. '
    "Include suggestion only for a concrete single-line fix on an anchored line; "
    "one physical line only — omit for architectural or multi-hunk fixes. "
    "Do not include style or lint findings. Return only valid JSON. "
    "Prioritize issues in the unified diff hunks below; use supplemental context "
    "only to validate cross-file impact."
)

JUDGE_SYSTEM_PROMPT = (
    "You are a verification judge for automated code review, not the primary reviewer. "
    "You receive ONE finding already produced by Moonshot (Kimi). Decide whether that "
    "specific finding is supported by the code evidence provided. "
    "Do NOT search for additional bugs or perform a full PR review. "
    "Do NOT uphold findings based on style or issues outside the cited claim. "
    "Uphold only when the evidence excerpt supports the severity and message. "
    "If evidence is missing or too thin, prefer dismissed or modified "
    "(modified = real issue but overstated severity). "
    "Return JSON only: "
    '{"outcome":"upheld|dismissed|modified","notes":"brief rationale tied to evidence"}'
)

VERIFICATION_JUDGE_SYSTEM_PROMPT = (
    "You verify whether an automated code review finding from a PRIOR revision "
    "is still valid given ONLY the push delta (changes since that revision). "
    "Original claim from prior revision — still valid on this push delta? "
    "Dismiss only when the push delta shows the issue was fixed or the claim no longer holds. "
    "Uphold when the delta does not refute the finding. "
    "Do not search for new issues. Return JSON only: "
    '{"outcome":"upheld|dismissed","notes":"brief rationale tied to push delta evidence"}'
)


@dataclass(frozen=True, slots=True)
class _AnthropicProfile:
    messages_url: str
    auth_headers: dict[str, str]
    model_id: str
    label: str


def _anthropic_base_headers() -> dict[str, str]:
    return {
        "anthropic-version": ANTHROPIC_VERSION,
        "Content-Type": "application/json",
    }


def _direct_profile(model_id: str) -> _AnthropicProfile | None:
    api_key = settings.anthropic_api_key
    if not api_key or not api_key.strip():
        return None
    return _AnthropicProfile(
        messages_url=ANTHROPIC_DIRECT_MESSAGES_URL,
        auth_headers={"x-api-key": api_key.strip()},
        model_id=model_id,
        label="direct",
    )


def _gateway_profile(fallback_model_id: str) -> _AnthropicProfile | None:
    messages_url = settings.anthropic_gateway_messages_url
    token = settings.anthropic_auth_token
    if not messages_url or not token or not token.strip():
        return None
    model_id = settings.effective_anthropic_gateway_judge_model or fallback_model_id
    return _AnthropicProfile(
        messages_url=messages_url,
        auth_headers={"Authorization": f"Bearer {token.strip()}"},
        model_id=model_id,
        label="gateway",
    )


def _judge_profiles(model_id: str | None) -> list[_AnthropicProfile]:
    resolved_model = model_id or settings.revy_anthropic_model
    profiles: list[_AnthropicProfile] = []
    gateway = _gateway_profile(resolved_model)
    if gateway is not None:
        profiles.append(gateway)
    direct = _direct_profile(resolved_model)
    if direct is not None:
        profiles.append(direct)
    return profiles


def _require_anthropic_direct_enabled() -> None:
    if not settings.anthropic_direct_enabled:
        raise ServiceUnavailableError(
            message="Anthropic API is not configured",
            error_code="llm_disabled",
        )


def _require_judge_anthropic_enabled() -> None:
    if not settings.anthropic_gateway_enabled and not settings.anthropic_direct_enabled:
        raise ServiceUnavailableError(
            message="Anthropic judge API is not configured",
            error_code="llm_disabled",
        )


def _extract_message_text(data: dict) -> str:
    content_blocks = data.get("content")
    if not isinstance(content_blocks, list) or not content_blocks:
        raise ServiceUnavailableError(
            message="Anthropic response invalid",
            error_code="llm_error",
        )
    first = content_blocks[0]
    if not isinstance(first, dict):
        raise ServiceUnavailableError(
            message="Anthropic response invalid",
            error_code="llm_error",
        )
    text = first.get("text")
    if not isinstance(text, str) or not text.strip():
        raise ServiceUnavailableError(
            message="Anthropic response invalid",
            error_code="llm_error",
        )
    return text


async def _post_anthropic_messages(
    client: httpx.AsyncClient,
    profile: _AnthropicProfile,
    *,
    system: str,
    user_prompt: str,
    max_tokens: int,
    timeout_seconds: float,
    output_config: dict | None = None,
) -> str:
    headers = {**_anthropic_base_headers(), **profile.auth_headers}
    body: dict[str, object] = {
        "model": profile.model_id,
        "max_tokens": max_tokens,
        "system": system,
        "messages": [{"role": "user", "content": user_prompt}],
    }
    if output_config is not None:
        body["output_config"] = output_config
    response = await client.post(
        profile.messages_url,
        headers=headers,
        json=body,
        timeout=timeout_seconds,
    )
    response.raise_for_status()
    data = response.json()
    if not isinstance(data, dict):
        raise ServiceUnavailableError(
            message="Anthropic response invalid",
            error_code="llm_error",
        )
    return _extract_message_text(data)


async def _post_with_profile_fallback(
    client: httpx.AsyncClient,
    profiles: list[_AnthropicProfile],
    *,
    system: str,
    user_prompt: str,
    max_tokens: int,
    timeout_seconds: float,
) -> str:
    if not profiles:
        raise ServiceUnavailableError(
            message="Anthropic API is not configured",
            error_code="llm_disabled",
        )
    last_exc: Exception | None = None
    for index, profile in enumerate(profiles):
        try:
            return await _post_anthropic_messages(
                client,
                profile,
                system=system,
                user_prompt=user_prompt,
                max_tokens=max_tokens,
                timeout_seconds=timeout_seconds,
            )
        except (httpx.HTTPError, ServiceUnavailableError) as exc:
            last_exc = exc
            if index < len(profiles) - 1:
                logger.warning(
                    "anthropic_profile_failed_trying_fallback",
                    extra={
                        "profile": profile.label,
                        "model_id": profile.model_id,
                        "error": str(exc),
                    },
                )
    if last_exc is not None:
        raise last_exc
    raise ServiceUnavailableError(
        message="Anthropic API is not configured",
        error_code="llm_disabled",
    )


async def complete_review(
    client: httpx.AsyncClient,
    *,
    user_prompt: str,
    model_id: str | None = None,
    timeout_seconds: float | None = None,
) -> str:
    _require_anthropic_direct_enabled()
    profile = _direct_profile(model_id or settings.revy_anthropic_model)
    if profile is None:
        raise ServiceUnavailableError(
            message="Anthropic API is not configured",
            error_code="llm_disabled",
        )
    return await _post_anthropic_messages(
        client,
        profile,
        system=REVIEW_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        max_tokens=4096,
        timeout_seconds=timeout_seconds or settings.revy_revision_timeout_standard_seconds,
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


async def judge_finding(
    client: httpx.AsyncClient,
    *,
    user_prompt: str,
    model_id: str | None = None,
    timeout_seconds: float | None = None,
    system_prompt: str | None = None,
) -> dict:
    _require_judge_anthropic_enabled()
    profiles = _judge_profiles(model_id)
    text = await _post_with_profile_fallback(
        client,
        profiles,
        system=system_prompt or JUDGE_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        max_tokens=1024,
        timeout_seconds=timeout_seconds or settings.revy_revision_timeout_standard_seconds,
    )
    return parse_judge_payload(text)


def build_verification_judge_prompt(
    *,
    group: object,
    push_delta_patch: str | None,
    evidence_snippet: str | None,
    start_line: int | None = None,
    end_line: int | None = None,
) -> str:
    title = getattr(group, "title", "")
    severity = stored_enum_value(getattr(group, "severity", ""))
    category = stored_enum_value(getattr(group, "category", ""))
    file_path = getattr(group, "file_path", None) or "n/a"
    message = getattr(group, "message", "")
    parts = [
        "Original finding from prior revision — is it still valid on this push delta?",
        "",
        f"Title: {title}",
        f"Severity: {severity}",
        f"Category: {category}",
        f"File: {file_path}",
        f"Message: {message}",
    ]
    if start_line is not None:
        line_ref = str(start_line)
        if end_line is not None and end_line != start_line:
            line_ref = f"{start_line}-{end_line}"
        parts.append(f"Line: {line_ref}")
    from app.services.github_finding_judge import resolve_judge_prompt_file_patch

    prompt_patch = resolve_judge_prompt_file_patch(evidence_snippet, push_delta_patch)
    if prompt_patch:
        parts.extend(["", "Push delta (since prior revision):", prompt_patch])
    if evidence_snippet:
        parts.extend(["", "Evidence excerpt:", evidence_snippet])
    return "\n".join(parts)


def parse_judge_outcome(raw: dict) -> tuple[str, str | None]:
    outcome = str(raw.get("outcome", "")).strip().lower()
    if outcome not in ("upheld", "dismissed", "modified"):
        raise ValueError("judge_outcome_invalid")
    notes = raw.get("notes")
    return outcome, notes.strip() if isinstance(notes, str) and notes.strip() else None


def judge_outcome_json_schema() -> dict[str, object]:
    """JSON schema for judge structured-output smoke (P0) and production wiring (P3)."""
    return {
        "type": "object",
        "properties": {
            "outcome": {
                "type": "string",
                "enum": ["upheld", "dismissed", "modified"],
            },
            "notes": {"type": "string"},
        },
        "required": ["outcome"],
        "additionalProperties": False,
    }


def judge_structured_output_config() -> dict[str, object]:
    # GA Anthropic shape: type + schema only (no format.name). RTU/LiteLLM gateway
    # rejects structured_outputs entirely; adding name is an extra field on that path.
    return {
        "format": {
            "type": "json_schema",
            "schema": judge_outcome_json_schema(),
        }
    }


async def _post_structured_judge_smoke(
    client: httpx.AsyncClient,
    profile: _AnthropicProfile,
    *,
    user_prompt: str,
    system_prompt: str | None = None,
    max_tokens: int = 1024,
    timeout_seconds: float | None = None,
) -> str:
    """P0 smoke — structured judge JSON via output_config (promoted in P3)."""
    return await _post_anthropic_messages(
        client,
        profile,
        system=system_prompt or JUDGE_SYSTEM_PROMPT,
        user_prompt=user_prompt,
        max_tokens=max_tokens,
        timeout_seconds=timeout_seconds or settings.revy_revision_timeout_standard_seconds,
        output_config=judge_structured_output_config(),
    )
