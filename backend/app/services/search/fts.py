# backend/app/services/search/fts.py
"""Text search helpers — extend per SEARCH.md. KP reference: backend/app/services/search/fts.py."""
from __future__ import annotations

import re
import unicodedata

_NON_WORD = re.compile(r"[^\w\s]", re.UNICODE)

_SMART_QUOTES = str.maketrans(
    {
        "\u2018": "'",
        "\u2019": "'",
        "\u201c": '"',
        "\u201d": '"',
        "\u201e": '"',
    }
)


def normalize_search_text(value: str) -> str:
    """Normalize user input before FTS or ILIKE (NFC, quotes, NBSP, zero-width)."""
    text = unicodedata.normalize("NFC", value)
    text = text.translate(_SMART_QUOTES)
    text = text.replace("\u00a0", " ")
    for ch in ("\u200b", "\u200c", "\u200d", "\ufeff", "\u00ad"):
        text = text.replace(ch, "")
    text = text.replace("''", "'")
    return " ".join(text.split())


def build_tsquery(raw: str) -> str | None:
    """Build a PostgreSQL tsquery string (AND-joined tokens). Returns None if empty."""
    normalized = normalize_search_text(raw)
    tokens = [t for t in _NON_WORD.sub(" ", normalized).split() if t]
    if not tokens:
        return None
    parts: list[str] = []
    for token in tokens:
        if len(token) >= 3:
            parts.append(f"{token}:*")
        else:
            parts.append(token)
    return " & ".join(parts)


def ilike_pattern(raw: str) -> str:
    """Safe-ish ILIKE wrapper after normalization (caller still parameterizes SQL)."""
    return f"%{normalize_search_text(raw)}%"
