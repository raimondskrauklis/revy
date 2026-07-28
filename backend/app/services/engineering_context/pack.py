# backend/app/services/engineering_context/pack.py
"""Orchestrate engineering context load + extract (RCX P1)."""
from __future__ import annotations

from dataclasses import dataclass, field

import httpx

from app.core.config import settings
from app.core.exceptions import (
    NotFoundError,
    RateLimitedError,
    ServiceUnavailableError,
    ValidationError,
)
from app.integrations.github_api import fetch_repository_file_at_sha
from app.services.engineering_context.extract import extract_engineering_context
from app.services.engineering_context.loader import load_review_context_manifest_at_sha
from app.services.engineering_context.scope import (
    program_applies_to_changed_files,
    resolve_active_program,
)


@dataclass
class EngineeringContextPack:
    active_program: str | None = None
    lock_ids: list[str] = field(default_factory=list)
    extracted_text: str = ""
    source_paths: list[str] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)


async def build_engineering_context_pack(
    client: httpx.AsyncClient,
    *,
    github_installation_id: int,
    owner: str,
    repo: str,
    head_sha: str,
    changed_files: frozenset[str] | list[str],
) -> EngineeringContextPack:
    pack = EngineeringContextPack()
    try:
        manifest = await load_review_context_manifest_at_sha(
            client,
            github_installation_id=github_installation_id,
            owner=owner,
            repo=repo,
            head_sha=head_sha,
        )
    except NotFoundError:
        pack.errors.append("review_context_ssot_not_found")
        return pack
    except (ValidationError, ValueError) as exc:
        pack.errors.append(str(exc))
        return pack
    except (RateLimitedError, ServiceUnavailableError, httpx.HTTPError) as exc:
        pack.errors.append(str(exc))
        return pack

    try:
        program = resolve_active_program(manifest)
    except ValidationError as exc:
        pack.errors.append(exc.error_code or str(exc))
        return pack

    if not program_applies_to_changed_files(program, changed_files):
        return pack

    pack.active_program = manifest.active_program
    max_bytes = settings.revy_engineering_context_max_bytes

    merged_parts: list[str] = []
    lock_ids: list[str] = []

    for path_entry in program.paths:
        try:
            md_text = await fetch_repository_file_at_sha(
                client,
                github_installation_id=github_installation_id,
                owner=owner,
                repo=repo,
                path=path_entry.path,
                ref=head_sha,
            )
        except NotFoundError:
            pack.errors.append(f"missing_path:{path_entry.path}")
            continue
        except (RateLimitedError, ServiceUnavailableError, httpx.HTTPError, UnicodeDecodeError) as exc:
            pack.errors.append(f"fetch_failed:{path_entry.path}:{exc}")
            continue

        result = extract_engineering_context(md_text, max_bytes=max_bytes)
        if result.text:
            merged_parts.append(result.text)
            pack.source_paths.append(path_entry.path)
        for lock_id in result.lock_ids:
            if lock_id not in lock_ids:
                lock_ids.append(lock_id)

    pack.lock_ids = lock_ids
    merged = "\n\n".join(merged_parts).strip()
    if len(merged.encode("utf-8")) > max_bytes:
        encoded = merged.encode("utf-8")[:max_bytes]
        merged = encoded.decode("utf-8", errors="ignore")
    pack.extracted_text = merged
    return pack
