# backend/app/services/code_chunking.py
"""Source file chunking for indexing — R3."""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import PurePosixPath

MAX_CHUNK_CHARS = 2000

SKIP_DIR_NAMES = frozenset({
    ".git",
    "node_modules",
    "vendor",
    "__pycache__",
    ".venv",
    "venv",
    "dist",
    "build",
    ".next",
    "coverage",
})

CODE_EXTENSIONS = frozenset({
    ".py",
    ".ts",
    ".tsx",
    ".js",
    ".jsx",
    ".go",
    ".rs",
    ".java",
    ".kt",
    ".md",
    ".json",
    ".yaml",
    ".yml",
    ".toml",
    ".sql",
    ".css",
    ".html",
})


@dataclass(frozen=True)
class CodeChunk:
    file_path: str
    chunk_index: int
    content: str


def should_index_file(file_path: str) -> bool:
    path = PurePosixPath(file_path.replace("\\", "/"))
    for part in path.parts:
        if part in SKIP_DIR_NAMES:
            return False
    suffix = path.suffix.lower()
    return suffix in CODE_EXTENSIONS


def chunk_file_content(file_path: str, content: str) -> list[CodeChunk]:
    if not content.strip():
        return []

    lines = content.splitlines()
    chunks: list[CodeChunk] = []
    buffer: list[str] = []
    buffer_len = 0
    chunk_index = 0

    def flush() -> None:
        nonlocal chunk_index, buffer, buffer_len
        if not buffer:
            return
        text = "\n".join(buffer).strip()
        if text:
            chunks.append(CodeChunk(file_path=file_path, chunk_index=chunk_index, content=text))
            chunk_index += 1
        buffer = []
        buffer_len = 0

    for line in lines:
        line_len = len(line) + 1
        if buffer and buffer_len + line_len > MAX_CHUNK_CHARS:
            flush()
        buffer.append(line)
        buffer_len += line_len

    flush()
    return chunks
