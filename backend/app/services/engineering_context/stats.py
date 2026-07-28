# backend/app/services/engineering_context/stats.py
"""Retrieve manifest + context_stats field contract (RCX P0 — populated in P2)."""
from __future__ import annotations

from typing import Any, TypedDict

from app.core.config import settings
from app.services.engineering_context.pack import EngineeringContextPack


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


def build_context_stats(
    *,
    engineering_pack: EngineeringContextPack,
    prompt_chars: int,
    unified_diff_bytes: int,
    diff_truncated: bool,
    omitted_files: list[str],
    diff_max_bytes: int | None = None,
) -> ContextStats:
    omitted_md = [path for path in omitted_files if path.endswith(".md")]
    inject_bytes = len(engineering_pack.inject_text.encode("utf-8"))
    return ContextStats(
        active_program=engineering_pack.active_program,
        diff_max_bytes=diff_max_bytes if diff_max_bytes is not None else default_diff_max_bytes(),
        unified_diff_bytes=unified_diff_bytes,
        diff_truncated=diff_truncated,
        omitted_files_count=len(omitted_files),
        omitted_md_count=len(omitted_md),
        engineering_context_injected=bool(engineering_pack.inject_text.strip()),
        engineering_context_bytes=inject_bytes,
        engineering_context_deduped_paths=list(engineering_pack.deduped_paths),
        lock_ids_extracted=list(engineering_pack.lock_ids),
        prompt_chars=prompt_chars,
    )
