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
    assert manifest.active_program == "revy-review-dogfood"
    assert len(manifest.programs) == 1
    active = manifest.programs[0]
    assert active.id == manifest.active_program
    assert active.scope == ("backend/**",)
    assert len(active.paths) == 3


def test_parse_review_context_manifest_rejects_multiple_programs():
    with pytest.raises(ValueError, match="exactly one entry"):
        parse_review_context_manifest(
            {
                "active_program": "a",
                "programs": [
                    {
                        "id": "a",
                        "scope": ["backend/**"],
                        "paths": [{"path": "docs/a.md", "description": "a"}],
                    },
                    {
                        "id": "b",
                        "scope": ["backend/**"],
                        "paths": [{"path": "docs/b.md", "description": "b"}],
                    },
                ],
            }
        )


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
