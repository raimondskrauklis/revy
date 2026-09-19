# backend/tests/unit/test_generate_greptile_files.py
"""RCX P3 — Greptile files.json generator drift check."""
import json

from scripts.generate_greptile_files_from_review_context import (
    GREPTILE_FILES_RELATIVE_PATH,
    build_greptile_files_payload,
    main,
    repo_root,
)


def test_generate_greptile_files_check_matches_committed():
    assert main(["--check", "--repo-root", str(repo_root())]) == 0


def test_generate_greptile_files_payload_matches_committed_shape():
    root = repo_root()
    payload = build_greptile_files_payload(root)
    assert "files" in payload
    for entry in payload["files"]:
        assert {"path", "description", "scope"} <= set(entry.keys())
        assert entry["scope"]
        assert set(entry["scope"]) <= {"backend/**", "frontend/**"}

    committed = json.loads((root / GREPTILE_FILES_RELATIVE_PATH).read_text(encoding="utf-8"))
    assert payload == committed
