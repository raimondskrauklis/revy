# backend/app/services/engineering_context/types.py
"""Review engineering context — SSOT manifest types (RCX P0)."""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ProgramPathEntry:
    path: str
    description: str


@dataclass(frozen=True)
class ProgramEntry:
    id: str
    scope: tuple[str, ...]
    paths: tuple[ProgramPathEntry, ...]


@dataclass(frozen=True)
class ReviewContextManifest:
    active_program: str
    programs: tuple[ProgramEntry, ...]
