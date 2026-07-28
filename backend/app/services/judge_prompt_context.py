# backend/app/services/judge_prompt_context.py
"""Shared judge prompt assembly helpers — snippet-first patch tier."""
from __future__ import annotations

from app.services.engineering_context.pack import EngineeringContextPack

JUDGE_PROMPT_PATCH_MAX_CHARS = 2048
JUDGE_ENGINEERING_CONTEXT_MAX_CHARS = 2048


def _truncate_judge_prompt_patch(patch: str) -> str:
    if len(patch) <= JUDGE_PROMPT_PATCH_MAX_CHARS:
        return patch
    return patch[:JUDGE_PROMPT_PATCH_MAX_CHARS]


def resolve_judge_prompt_file_patch(
    evidence_snippet: str | None,
    file_patch: str | None,
) -> str | None:
    """Snippet-first tier: omit patch when evidence excerpt is present."""
    if not file_patch:
        return None
    if evidence_snippet and evidence_snippet.strip():
        return None
    return _truncate_judge_prompt_patch(file_patch)


def judge_prompt_file_patch_chars(
    evidence_snippet: str | None,
    file_patch: str | None,
) -> int | None:
    prompt_patch = resolve_judge_prompt_file_patch(evidence_snippet, file_patch)
    return len(prompt_patch) if prompt_patch else None


def _truncate_utf8(text: str, max_bytes: int) -> str:
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text
    return encoded[:max_bytes].decode("utf-8", errors="ignore")


def format_judge_engineering_context(
    pack: EngineeringContextPack | None,
    *,
    max_chars: int = JUDGE_ENGINEERING_CONTEXT_MAX_CHARS,
) -> str | None:
    if pack is None:
        return None
    text = pack.extracted_text.strip()
    if not text:
        return None
    return _truncate_utf8(text, max_chars)
