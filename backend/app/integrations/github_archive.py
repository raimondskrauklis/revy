# backend/app/integrations/github_archive.py
"""GitHub repository tarball download and safe extract — R3 indexing."""
from __future__ import annotations

import io
import tarfile
from pathlib import Path

import httpx

from app.integrations.github_api import GITHUB_API_BASE, create_installation_access_token
from app.services.code_chunking import should_index_file


def _is_safe_tar_member(member: tarfile.TarInfo) -> bool:
    name = member.name.replace("\\", "/")
    return not (name.startswith("/") or ".." in Path(name).parts)


def extract_tarball(archive_bytes: bytes, destination: Path) -> Path:
    destination.mkdir(parents=True, exist_ok=True)
    root_dir: Path | None = None

    with tarfile.open(fileobj=io.BytesIO(archive_bytes), mode="r:gz") as tar:
        for member in tar.getmembers():
            if not _is_safe_tar_member(member):
                continue
            tar.extract(member, path=destination, filter="data")
            if root_dir is None and member.isdir():
                root_dir = destination / member.name

    if root_dir is None:
        children = [p for p in destination.iterdir() if p.is_dir()]
        if len(children) == 1:
            return children[0]
        return destination
    return root_dir


async def download_repository_tarball(
    client: httpx.AsyncClient,
    *,
    github_installation_id: int,
    owner: str,
    repo: str,
    ref: str,
) -> bytes:
    token = await create_installation_access_token(
        client,
        github_installation_id=github_installation_id,
    )
    response = await client.get(
        f"{GITHUB_API_BASE}/repos/{owner}/{repo}/tarball/{ref}",
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
        },
        follow_redirects=True,
    )
    response.raise_for_status()
    return response.content


def iter_indexable_files(root_dir: Path) -> list[tuple[str, str]]:
    files: list[tuple[str, str]] = []
    for path in sorted(root_dir.rglob("*")):
        if not path.is_file():
            continue
        rel = path.relative_to(root_dir).as_posix()
        if not should_index_file(rel):
            continue
        try:
            content = path.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        files.append((rel, content))
    return files
