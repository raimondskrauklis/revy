# backend/tests/unit/test_github_suggestion.py
"""GitHub suggestion eligibility — polish."""
from types import SimpleNamespace

from app.services import github_suggestion


def test_is_publishable_suggestion_accepts_valid():
    finding = SimpleNamespace(
        suggestion="return True",
        file_path="app/main.py",
        start_line=4,
        end_line=None,
    )
    assert github_suggestion.is_publishable_suggestion(finding) == "return True"


def test_is_publishable_suggestion_preserves_leading_indent():
    finding = SimpleNamespace(
        suggestion="    return True",
        file_path="app/main.py",
        start_line=4,
        end_line=None,
    )
    assert github_suggestion.is_publishable_suggestion(finding) == "    return True"


def test_is_publishable_suggestion_rejects_newline():
    finding = SimpleNamespace(
        suggestion="a\nb",
        file_path="app/main.py",
        start_line=4,
        end_line=None,
    )
    assert github_suggestion.is_publishable_suggestion(finding) is None


def test_is_publishable_suggestion_rejects_fence_chars():
    finding = SimpleNamespace(
        suggestion="```evil```",
        file_path="app/main.py",
        start_line=4,
        end_line=None,
    )
    assert github_suggestion.is_publishable_suggestion(finding) is None


def test_is_publishable_suggestion_rejects_multiline_anchor():
    finding = SimpleNamespace(
        suggestion="return True",
        file_path="app/main.py",
        start_line=4,
        end_line=8,
    )
    assert github_suggestion.is_publishable_suggestion(finding) is None
