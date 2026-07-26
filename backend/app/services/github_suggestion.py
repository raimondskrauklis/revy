# backend/app/services/github_suggestion.py
"""GitHub inline suggestion eligibility — review pipeline polish."""
from __future__ import annotations

from typing import Protocol

SUGGESTION_MAX_LENGTH = 2000


class SuggestionFinding(Protocol):
    suggestion: str | None
    file_path: str | None
    start_line: int | None
    end_line: int | None


def normalize_end_line(end_line: int | None) -> int | None:
    if end_line == 0:
        return None
    return end_line


def is_eligible_suggestion_text(suggestion: str | None) -> str | None:
    if not isinstance(suggestion, str):
        return None
    if not suggestion.strip():
        return None
    if "\n" in suggestion or "\r" in suggestion:
        return None
    if "```" in suggestion:
        return None
    if len(suggestion) > SUGGESTION_MAX_LENGTH:
        return None
    return suggestion


def is_single_line_anchor(*, start_line: int | None, end_line: int | None) -> bool:
    if start_line is None:
        return False
    normalized_end = normalize_end_line(end_line)
    return normalized_end is None or normalized_end == start_line


def validated_suggestion_for_row(
    *,
    suggestion: object,
    file_path: str | None,
    start_line: int | None,
    end_line: int | None,
) -> str | None:
    text = is_eligible_suggestion_text(suggestion if isinstance(suggestion, str) else None)
    if text is None:
        return None
    if file_path is None or start_line is None:
        return None
    if not is_single_line_anchor(start_line=start_line, end_line=end_line):
        return None
    return text


def is_publishable_suggestion(finding: SuggestionFinding) -> str | None:
    return validated_suggestion_for_row(
        suggestion=finding.suggestion,
        file_path=finding.file_path,
        start_line=finding.start_line,
        end_line=finding.end_line,
    )
