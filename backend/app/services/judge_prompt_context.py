# backend/app/services/judge_prompt_context.py
"""Shared judge prompt assembly helpers — snippet-first patch tier."""
from __future__ import annotations

JUDGE_PROMPT_PATCH_MAX_CHARS = 2048


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
