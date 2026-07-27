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
    '"file_path":"optional/path","start_line":0,"end_line":0,'
    '"suggestion":"optional single-line replacement or omit"}]}. '
    "Include suggestion only for a concrete single-line fix on an anchored line; "
    "one physical line only — omit for architectural or multi-hunk fixes. "
    "Do not include style or lint findings. Return only valid JSON. "
    "Prioritize issues in the unified diff hunks below; use supplemental context "
    "only to validate cross-file impact."
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
    model_id: str | None = None,
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
            "model": model_id or settings.revy_anthropic_model,
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


JUDGE_SYSTEM_PROMPT = (
    "You are an expert code review judge. Given a finding, decide whether it should be "
    "upheld, dismissed as a false positive, or modified. Return JSON only: "
    '{"outcome":"upheld|dismissed|modified","notes":"brief rationale"}'
)


async def judge_finding(
    client: httpx.AsyncClient,
    *,
    user_prompt: str,
    model_id: str | None = None,
    timeout_seconds: float | None = None,
) -> dict:
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
            "model": model_id or settings.revy_anthropic_model,
            "max_tokens": 1024,
            "system": JUDGE_SYSTEM_PROMPT,
            "messages": [{"role": "user", "content": user_prompt}],
        },
        timeout=timeout_seconds or settings.revy_revision_timeout_standard_seconds,
    )
    response.raise_for_status()
    data = response.json()
    content_blocks = data.get("content")
    if not isinstance(content_blocks, list) or not content_blocks:
        raise ServiceUnavailableError(
            message="Anthropic judge response invalid",
            error_code="llm_error",
        )
    first = content_blocks[0]
    if not isinstance(first, dict):
        raise ServiceUnavailableError(
            message="Anthropic judge response invalid",
            error_code="llm_error",
        )
    text = first.get("text")
    if not isinstance(text, str) or not text.strip():
        raise ServiceUnavailableError(
            message="Anthropic judge response invalid",
            error_code="llm_error",
        )
    payload = json.loads(text)
    if not isinstance(payload, dict):
        raise ValueError("judge_json_not_object")
    return payload


def parse_judge_outcome(raw: dict) -> tuple[str, str | None]:
    outcome = str(raw.get("outcome", "")).strip().lower()
    if outcome not in ("upheld", "dismissed", "modified"):
        raise ValueError("judge_outcome_invalid")
    notes = raw.get("notes")
    return outcome, notes.strip() if isinstance(notes, str) and notes.strip() else None
