# backend/app/services/engineering_context/stats.py
"""Retrieve manifest + context_stats field contract (RCX P0 — populated in P2)."""
from __future__ import annotations

from typing import Any, TypedDict

from app.core.config import settings


class ContextStats(TypedDict, total=False):
    active_program: str | None
    diff_max_bytes: int
    unified_diff_bytes: int
    diff_truncated: bool
    omitted_files_count: int
    omitted_md_count: int
    engineering_context_injected: bool
    engineering_context_bytes: int
    engineering_context_deduped_paths: list[str]
    lock_ids_extracted: list[str]
    prompt_chars: int


def default_diff_max_bytes() -> int:
    return settings.revy_diff_max_bytes


def engineering_context_manifest_defaults(
    *,
    diff_max_bytes: int | None = None,
) -> dict[str, Any]:
    cap = diff_max_bytes if diff_max_bytes is not None else default_diff_max_bytes()
    return {
        "engineering_context_injected": False,
        "engineering_context_bytes": 0,
        "diff_max_bytes": cap,
        "unified_diff_bytes": 0,
        "active_program": None,
        "lock_ids_extracted": [],
        "engineering_context_deduped_paths": [],
    }


def empty_context_stats() -> ContextStats:
    return ContextStats(
        active_program=None,
        diff_max_bytes=default_diff_max_bytes(),
        unified_diff_bytes=0,
        diff_truncated=False,
        omitted_files_count=0,
        omitted_md_count=0,
        engineering_context_injected=False,
        engineering_context_bytes=0,
        engineering_context_deduped_paths=[],
        lock_ids_extracted=[],
        prompt_chars=0,
    )
