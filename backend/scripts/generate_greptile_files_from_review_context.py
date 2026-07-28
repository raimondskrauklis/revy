# backend/scripts/generate_greptile_files_from_review_context.py
"""Generate `.greptile/files.json` from SSOT `.greptile/review-context.json` (RCX P3)."""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from app.core.exceptions import ValidationError
from app.services.engineering_context.manifest import (
    SSOT_RELATIVE_PATH,
    parse_review_context_manifest_json,
)
from app.services.engineering_context.scope import resolve_active_program
from app.services.engineering_context.validate import validate_review_context_paths_exist

GREPTILE_FILES_RELATIVE_PATH = ".greptile/files.json"


def repo_root() -> Path:
    return Path(__file__).resolve().parents[2]


def build_greptile_files_payload(repo_root_path: Path) -> dict[str, list[dict[str, object]]]:
    ssot_path = repo_root_path / SSOT_RELATIVE_PATH
    if not ssot_path.is_file():
        raise SystemExit(f"SSOT not found: {ssot_path}")

    manifest = parse_review_context_manifest_json(ssot_path.read_text(encoding="utf-8"))
    missing = validate_review_context_paths_exist(manifest, repo_root_path)
    if missing:
        raise SystemExit(f"SSOT paths missing on disk: {missing}")

    try:
        program = resolve_active_program(manifest)
    except ValidationError as exc:
        raise SystemExit(str(exc)) from exc

    files = [
        {
            "path": entry.path,
            "description": entry.description,
            "scope": list(program.scope),
        }
        for entry in program.paths
    ]
    return {"files": files}


def write_files_json(repo_root_path: Path, payload: dict[str, list[dict[str, object]]]) -> Path:
    target = repo_root_path / GREPTILE_FILES_RELATIVE_PATH
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return target


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Generate Greptile files.json from RCX SSOT")
    parser.add_argument(
        "--check",
        action="store_true",
        help="Verify committed files.json matches generator output",
    )
    parser.add_argument(
        "--write",
        action="store_true",
        help="Write .greptile/files.json from SSOT",
    )
    parser.add_argument(
        "--repo-root",
        type=Path,
        default=None,
        help="Repository root (default: parent of backend/)",
    )
    args = parser.parse_args(argv)

    if not args.check and not args.write:
        parser.error("Specify --check or --write")

    root = args.repo_root or repo_root()
    payload = build_greptile_files_payload(root)

    if args.write:
        path = write_files_json(root, payload)
        print(f"Wrote {path}")
        return 0

    target = root / GREPTILE_FILES_RELATIVE_PATH
    if not target.is_file():
        print(f"Missing {target}", file=sys.stderr)
        return 1
    committed = json.loads(target.read_text(encoding="utf-8"))
    if committed != payload:
        print("files.json drift — run generate_greptile_files_from_review_context --write", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
