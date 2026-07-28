# backend/app/services/engineering_context/validate.py
"""SSOT path-exists validation (RCX P0)."""
from __future__ import annotations

from pathlib import Path

from app.services.engineering_context.types import ReviewContextManifest


def validate_review_context_paths_exist(
    manifest: ReviewContextManifest,
    repo_root: Path,
) -> list[str]:
    missing: list[str] = []
    for program in manifest.programs:
        for entry in program.paths:
            if not (repo_root / entry.path).is_file():
                missing.append(entry.path)
    return missing
