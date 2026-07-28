# backend/app/services/engineering_context/dedupe.py
"""RCX-D12 dedupe — skip full MD inject when path already in diff (RCX P2)."""
from __future__ import annotations


def _normalize_path(file_path: str) -> str:
    normalized = file_path.replace("\\", "/").strip()
    if normalized.startswith("./"):
        normalized = normalized[2:]
    return normalized


def _path_in_collection(path: str, paths: frozenset[str] | set[str] | list[str]) -> bool:
    normalized = _normalize_path(path)
    return any(candidate == path or _normalize_path(candidate) == normalized for candidate in paths)


def _lookup_patch(patches_by_file: dict[str, str], file_path: str) -> str | None:
    direct = patches_by_file.get(file_path)
    if direct is not None:
        return direct
    normalized = _normalize_path(file_path)
    if normalized != file_path:
        direct = patches_by_file.get(normalized)
        if direct is not None:
            return direct
    for key, patch in patches_by_file.items():
        if _normalize_path(key) == normalized:
            return patch
    return None


def should_skip_full_md_inject(
    path: str,
    changed_files: frozenset[str] | set[str] | list[str],
    omitted_files: frozenset[str] | set[str] | list[str],
    patches_by_file: dict[str, str],
) -> bool:
    """Skip full MD body when path is in diff with a patch and not omitted (RCX-D12)."""
    if not _path_in_collection(path, changed_files):
        return False
    if _path_in_collection(path, omitted_files):
        return False
    return _lookup_patch(patches_by_file, path) is not None
