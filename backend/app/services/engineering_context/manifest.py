# backend/app/services/engineering_context/manifest.py
"""Parse and validate `.greptile/review-context.json` SSOT (RCX P0)."""
from __future__ import annotations

import json
from typing import Any

from app.services.engineering_context.types import (
    ProgramEntry,
    ProgramPathEntry,
    ReviewContextManifest,
)

SSOT_RELATIVE_PATH = ".greptile/review-context.json"


def parse_review_context_manifest(raw: dict[str, Any]) -> ReviewContextManifest:
    active_program = str(raw.get("active_program", "")).strip()
    if not active_program:
        raise ValueError("active_program is required")

    programs_raw = raw.get("programs")
    if not isinstance(programs_raw, list) or not programs_raw:
        raise ValueError("programs must be a non-empty list")

    programs: list[ProgramEntry] = []
    for item in programs_raw:
        if not isinstance(item, dict):
            raise ValueError("program entry must be an object")
        program_id = str(item.get("id", "")).strip()
        if not program_id:
            raise ValueError("program id is required")

        scope_raw = item.get("scope")
        if not isinstance(scope_raw, list) or not scope_raw:
            raise ValueError(f"program {program_id}: scope must be a non-empty list")
        scope = tuple(str(s).strip() for s in scope_raw if str(s).strip())
        if not scope:
            raise ValueError(f"program {program_id}: scope must be a non-empty list")

        paths_raw = item.get("paths")
        if not isinstance(paths_raw, list) or not paths_raw:
            raise ValueError(f"program {program_id}: paths must be a non-empty list")
        paths: list[ProgramPathEntry] = []
        for path_item in paths_raw:
            if not isinstance(path_item, dict):
                raise ValueError(f"program {program_id}: path entry must be an object")
            path = str(path_item.get("path", "")).strip()
            description = str(path_item.get("description", "")).strip()
            if not path:
                raise ValueError(f"program {program_id}: path is required")
            paths.append(ProgramPathEntry(path=path, description=description))

        programs.append(
            ProgramEntry(id=program_id, scope=scope, paths=tuple(paths)),
        )

    program_ids = {program.id for program in programs}
    if active_program not in program_ids:
        raise ValueError("active_program must reference a programs[].id")

    return ReviewContextManifest(active_program=active_program, programs=tuple(programs))


def parse_review_context_manifest_json(text: str) -> ReviewContextManifest:
    raw = json.loads(text)
    if not isinstance(raw, dict):
        raise ValueError("SSOT root must be a JSON object")
    return parse_review_context_manifest(raw)
