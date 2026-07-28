# backend/tests/unit/test_engineering_context_dedupe.py
"""RCX P2 — RCX-D12 full-MD inject dedupe."""
from app.services.engineering_context.dedupe import should_skip_full_md_inject


def test_should_skip_full_md_inject_when_in_diff_with_patch():
    assert should_skip_full_md_inject(
        "docs/a.md",
        frozenset(["docs/a.md"]),
        frozenset(),
        {"docs/a.md": "patch"},
    )


def test_should_not_skip_when_not_in_changed_files():
    assert not should_skip_full_md_inject(
        "docs/a.md",
        frozenset(["backend/main.py"]),
        frozenset(),
        {"docs/a.md": "patch"},
    )


def test_should_not_skip_when_omitted():
    assert not should_skip_full_md_inject(
        "docs/a.md",
        frozenset(["docs/a.md"]),
        frozenset(["docs/a.md"]),
        {"docs/a.md": "patch"},
    )


def test_should_not_skip_when_no_patch():
    assert not should_skip_full_md_inject(
        "docs/a.md",
        frozenset(["docs/a.md"]),
        frozenset(),
        {},
    )
