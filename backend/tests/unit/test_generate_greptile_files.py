# backend/tests/unit/test_generate_greptile_files.py
"""RCX P3 — Greptile files.json generator."""
import json
import subprocess
import sys
from pathlib import Path

from scripts.generate_greptile_files_from_review_context import (
    build_greptile_files_payload,
    repo_root,
)

_REPO_ROOT = repo_root()


def test_build_greptile_files_payload_has_three_rcx_entries():
    payload = build_greptile_files_payload(_REPO_ROOT)
    files = payload["files"]
    assert len(files) == 3
    paths = {item["path"] for item in files}
    assert "docs/review-pipeline/review-engineering-context/waves/REVIEW_ENGINEERING_CONTEXT_EXECUTION.md" in paths
    for item in files:
        assert item["scope"] == ["backend/**"]
        assert item["description"]


def test_generate_greptile_files_check_passes_against_committed():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "scripts.generate_greptile_files_from_review_context",
            "--check",
        ],
        cwd=Path(__file__).resolve().parents[2],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, result.stderr


def test_committed_files_json_matches_generator_output():
    target = _REPO_ROOT / ".greptile/files.json"
    committed = json.loads(target.read_text(encoding="utf-8"))
    generated = build_greptile_files_payload(_REPO_ROOT)
    assert committed == generated
