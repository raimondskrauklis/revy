# backend/tests/unit/test_engineering_context_dedupe.py
"""RCX P2 — inject dedupe (RCX-D12)."""
from app.services.engineering_context.dedupe import should_skip_full_md_inject


def test_should_skip_full_md_when_in_diff_with_patch():
    assert should_skip_full_md_inject(
        "docs/plan.md",
        changed_files=["docs/plan.md"],
        omitted_files=[],
        patches_by_file={"docs/plan.md": "@@ patch"},
    )


def test_should_not_skip_when_path_omitted_from_diff():
    assert not should_skip_full_md_inject(
        "docs/plan.md",
        changed_files=["docs/plan.md"],
        omitted_files=["docs/plan.md"],
        patches_by_file={"docs/plan.md": "@@ patch"},
    )


def test_should_not_skip_when_path_not_in_diff():
    assert not should_skip_full_md_inject(
        "docs/plan.md",
        changed_files=["backend/main.py"],
        omitted_files=[],
        patches_by_file={"backend/main.py": "@@ patch"},
    )


def test_should_not_skip_when_changed_but_no_patch():
    assert not should_skip_full_md_inject(
        "docs/plan.md",
        changed_files=["docs/plan.md"],
        omitted_files=[],
        patches_by_file={},
    )
