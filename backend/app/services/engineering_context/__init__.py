# backend/app/services/engineering_context/__init__.py
"""Review engineering context — SSOT manifest and inject (RCX)."""
from app.services.engineering_context.manifest import (
    SSOT_RELATIVE_PATH,
    parse_review_context_manifest,
    parse_review_context_manifest_json,
)
from app.services.engineering_context.pack import (
    EngineeringContextPack,
    build_engineering_context_pack,
)
from app.services.engineering_context.stats import (
    ContextStats,
    empty_context_stats,
    engineering_context_manifest_defaults,
)
from app.services.engineering_context.types import (
    ProgramEntry,
    ProgramPathEntry,
    ReviewContextManifest,
)
from app.services.engineering_context.validate import validate_review_context_paths_exist

__all__ = [
    "SSOT_RELATIVE_PATH",
    "ContextStats",
    "EngineeringContextPack",
    "ProgramEntry",
    "ProgramPathEntry",
    "ReviewContextManifest",
    "build_engineering_context_pack",
    "empty_context_stats",
    "engineering_context_manifest_defaults",
    "parse_review_context_manifest",
    "parse_review_context_manifest_json",
    "validate_review_context_paths_exist",
]
