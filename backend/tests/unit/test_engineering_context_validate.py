# backend/tests/unit/test_engineering_context_validate.py
"""RCX P0 — SSOT path-exists validation."""
from pathlib import Path

from app.services.engineering_context.manifest import parse_review_context_manifest_json
from app.services.engineering_context.validate import validate_review_context_paths_exist


def test_validate_review_context_paths_exist_committed_ssot():
    repo_root = Path(__file__).resolve().parents[3]
    raw_text = (repo_root / ".greptile/review-context.json").read_text(encoding="utf-8")
    manifest = parse_review_context_manifest_json(raw_text)
    missing = validate_review_context_paths_exist(manifest, repo_root)
    assert missing == []


def test_validate_review_context_paths_exist_reports_missing():
    repo_root = Path(__file__).resolve().parents[3]
    manifest = parse_review_context_manifest_json(
        """
        {
          "active_program": "p",
          "programs": [
            {
              "id": "p",
              "scope": ["backend/**"],
              "paths": [{"path": "nonexistent/rcx/path.md", "description": "x"}]
            }
          ]
        }
        """
    )
    missing = validate_review_context_paths_exist(manifest, repo_root)
    assert missing == ["nonexistent/rcx/path.md"]


def test_validate_review_context_paths_exist_rejects_traversal():
    repo_root = Path(__file__).resolve().parents[3]
    manifest = parse_review_context_manifest_json(
        """
        {
          "active_program": "p",
          "programs": [
            {
              "id": "p",
              "scope": ["backend/**"],
              "paths": [{"path": "../../etc/passwd", "description": "x"}]
            }
          ]
        }
        """
    )
    missing = validate_review_context_paths_exist(manifest, repo_root)
    assert missing == ["../../etc/passwd"]
