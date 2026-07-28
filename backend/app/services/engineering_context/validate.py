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
    resolved_root = repo_root.resolve()
    for program in manifest.programs:
        for entry in program.paths:
            candidate = (repo_root / entry.path).resolve()
            try:
                candidate.relative_to(resolved_root)
            except ValueError:
                missing.append(entry.path)
                continue
            if not candidate.is_file():
                missing.append(entry.path)
    return missing
