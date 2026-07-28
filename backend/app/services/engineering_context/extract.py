# backend/app/services/engineering_context/extract.py
"""Lock/smoke extractor from findings MD (RCX P1)."""
from __future__ import annotations

import re
from dataclasses import dataclass

_LOCKED_DECISIONS_HEADING = re.compile(
    r"^## Locked decisions(?:\s+\([^)]+\))?\s*$",
    re.MULTILINE,
)
_SMOKE_HEADING = re.compile(
    r"^(?:## P0 smoke[^\n]*|### P0 smoke matrix|### Baseline captured)\s*$",
    re.MULTILINE,
)
_QUERIED_LINE = re.compile(r"^\*\*Queried:\*\*", re.MULTILINE)
_LOCK_ID_CELL = re.compile(r"^\|\s*\*\*([A-Z][A-Z0-9]*-D\d+)\*\*\s*\|", re.MULTILINE)
_LOCK_ID_PLAIN = re.compile(r"^\|\s*([A-Z][A-Z0-9]*-D\d+)\s*\|", re.MULTILINE)
_SECTION_BREAK = re.compile(r"^## ", re.MULTILINE)


@dataclass(frozen=True)
class ExtractResult:
    text: str
    lock_ids: tuple[str, ...]


def _truncate_utf8(text: str, max_bytes: int) -> str:
    encoded = text.encode("utf-8")
    if len(encoded) <= max_bytes:
        return text
    return encoded[:max_bytes].decode("utf-8", errors="ignore")


def _extract_lock_ids(section_text: str) -> list[str]:
    ids: list[str] = []
    seen: set[str] = set()
    for pattern in (_LOCK_ID_CELL, _LOCK_ID_PLAIN):
        for match in pattern.finditer(section_text):
            lock_id = match.group(1)
            if lock_id not in seen:
                seen.add(lock_id)
                ids.append(lock_id)
    return ids


def _section_span(md_text: str, start: int) -> tuple[str, int, int]:
    remainder = md_text[start:]
    break_match = _SECTION_BREAK.search(remainder, pos=1)
    end_offset = break_match.start() if break_match else len(remainder)
    section = remainder[:end_offset].strip()
    end_pos = start + end_offset
    return section, start, end_pos


def _overlaps_spans(spans: list[tuple[int, int]], start: int, end: int) -> bool:
    return any(start < span_end and end > span_start for span_start, span_end in spans)


def extract_engineering_context(md_text: str, *, max_bytes: int) -> ExtractResult:
    parts: list[str] = []
    lock_ids: list[str] = []
    covered: list[tuple[int, int]] = []

    def try_add(section: str, start: int, end: int, *, from_locked: bool = False) -> None:
        if not section or _overlaps_spans(covered, start, end):
            return
        parts.append(section)
        covered.append((start, end))
        if from_locked:
            lock_ids.extend(_extract_lock_ids(section))

    for match in _LOCKED_DECISIONS_HEADING.finditer(md_text):
        section, start, end = _section_span(md_text, match.start())
        try_add(section, start, end, from_locked=True)

    for match in _SMOKE_HEADING.finditer(md_text):
        section, start, end = _section_span(md_text, match.start())
        try_add(section, start, end)

    if "**Queried:**" not in "\n\n".join(parts):
        for match in _QUERIED_LINE.finditer(md_text):
            section, start, end = _section_span(md_text, match.start())
            try_add(section, start, end)

    merged = "\n\n".join(parts).strip()
    if not merged:
        return ExtractResult(text="", lock_ids=())

    unique_lock_ids = tuple(dict.fromkeys(lock_ids))
    return ExtractResult(
        text=_truncate_utf8(merged, max_bytes),
        lock_ids=unique_lock_ids,
    )
