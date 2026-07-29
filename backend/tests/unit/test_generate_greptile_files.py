# backend/tests/unit/test_generate_greptile_files.py
"""RCX P3 — Greptile files.json generator drift check."""
from scripts.generate_greptile_files_from_review_context import main, repo_root


def test_generate_greptile_files_check_matches_committed():
    assert main(["--check", "--repo-root", str(repo_root())]) == 0
