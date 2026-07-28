# backend/tests/unit/test_engineering_context_scope.py
"""RCX P1 — active program + scope filter."""
import pytest

from app.core.exceptions import ValidationError
from app.services.engineering_context.scope import (
    program_applies_to_changed_files,
    resolve_active_program,
)
from app.services.engineering_context.types import (
    ProgramEntry,
    ProgramPathEntry,
    ReviewContextManifest,
)


def _manifest() -> ReviewContextManifest:
    return ReviewContextManifest(
        active_program="review-engineering-context",
        programs=(
            ProgramEntry(
                id="review-engineering-context",
                scope=("backend/**",),
                paths=(ProgramPathEntry(path="docs/a.md", description="a"),),
            ),
        ),
    )


def test_resolve_active_program():
    program = resolve_active_program(_manifest())
    assert program.id == "review-engineering-context"


def test_resolve_active_program_missing_raises():
    manifest = ReviewContextManifest(active_program="other", programs=_manifest().programs)
    with pytest.raises(ValidationError):
        resolve_active_program(manifest)


def test_program_applies_to_changed_files():
    program = resolve_active_program(_manifest())
    assert program_applies_to_changed_files(program, ["backend/app/main.py"])
    assert not program_applies_to_changed_files(program, ["frontend/src/App.tsx"])
    assert not program_applies_to_changed_files(program, [])
