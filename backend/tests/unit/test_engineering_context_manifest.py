# backend/tests/unit/test_engineering_context_manifest.py
"""RCX P0 — SSOT manifest parser."""
from pathlib import Path

import pytest

from app.services.engineering_context.manifest import (
    SSOT_RELATIVE_PATH,
    parse_review_context_manifest,
    parse_review_context_manifest_json,
)


def test_parse_committed_ssot_file():
    repo_root = Path(__file__).resolve().parents[3]
    raw_text = (repo_root / SSOT_RELATIVE_PATH).read_text(encoding="utf-8")
    manifest = parse_review_context_manifest_json(raw_text)
    assert manifest.active_program == "review-engineering-context"
    assert len(manifest.programs) == 1
    program = manifest.programs[0]
    assert program.id == "review-engineering-context"
    assert program.scope == ("backend/**",)
    assert len(program.paths) == 3


def test_parse_review_context_manifest_requires_active_program():
    with pytest.raises(ValueError, match="active_program"):
        parse_review_context_manifest({"programs": []})


def test_parse_review_context_manifest_active_program_must_exist():
    with pytest.raises(ValueError, match="active_program must reference"):
        parse_review_context_manifest(
            {
                "active_program": "missing",
                "programs": [
                    {
                        "id": "other",
                        "scope": ["backend/**"],
                        "paths": [{"path": "docs/a.md", "description": "a"}],
                    }
                ],
            }
        )
