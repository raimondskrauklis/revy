# backend/app/services/engineering_context/scope.py
"""Active program resolution and scope filter (RCX P1)."""
from __future__ import annotations

import fnmatch

from app.core.exceptions import ValidationError
from app.services.engineering_context.types import ProgramEntry, ReviewContextManifest


def resolve_active_program(manifest: ReviewContextManifest) -> ProgramEntry:
    for program in manifest.programs:
        if program.id == manifest.active_program:
            return program
    raise ValidationError(
        message="active_program not found in programs",
        error_code="review_context_active_program_missing",
    )


def program_applies_to_changed_files(
    program: ProgramEntry,
    changed_files: frozenset[str] | list[str],
) -> bool:
    if not changed_files:
        return False
    for file_path in changed_files:
        normalized = file_path.replace("\\", "/")
        for pattern in program.scope:
            if fnmatch.fnmatch(normalized, pattern):
                return True
    return False
