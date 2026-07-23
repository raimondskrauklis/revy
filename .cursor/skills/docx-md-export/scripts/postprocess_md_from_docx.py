# .cursor/skills/docx-md-export/scripts/postprocess_md_from_docx.py
"""Post-process Pandoc GFM output for KP markdown conventions."""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

_PANDOC_ATTR = re.compile(r"\{[^{}]+\}")
_UNDERLINE_HTML = re.compile(r"</?u>", re.IGNORECASE)
_EMPTY_HTML_COMMENT = re.compile(r"^\s*<!--\s*-->\s*$")
_TRAILING_BACKSLASH = re.compile(r"\\$")


def _relative_path_comment(output_path: Path, root: Path) -> str:
    try:
        rel = output_path.resolve().relative_to(root.resolve())
        return f"# {rel.as_posix()}"
    except ValueError:
        return f"# {output_path.name}"


def postprocess(text: str) -> str:
    lines: list[str] = []
    for line in text.splitlines():
        if _EMPTY_HTML_COMMENT.match(line):
            continue
        line = _PANDOC_ATTR.sub("", line)
        line = _UNDERLINE_HTML.sub("", line)
        line = line.replace('\\"', '"')
        line = _TRAILING_BACKSLASH.sub("", line.rstrip())
        lines.append(line)

    # Collapse 3+ consecutive blank lines to 2
    out: list[str] = []
    blank_run = 0
    for line in lines:
        if not line.strip():
            blank_run += 1
            if blank_run <= 2:
                out.append("")
            continue
        blank_run = 0
        out.append(line)

    return "\n".join(out).strip() + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description="Post-process Pandoc docx→md output.")
    parser.add_argument("input", type=Path, help="Raw Pandoc markdown file")
    parser.add_argument("output", type=Path, help="Final markdown file")
    parser.add_argument("--root", type=Path, required=True, help="Repository root for path comment")
    args = parser.parse_args()

    raw = args.input.read_text(encoding="utf-8")
    body = postprocess(raw)
    header = _relative_path_comment(args.output, args.root)
    args.output.write_text(f"{header}\n\n{body}", encoding="utf-8")
    return 0


if __name__ == "__main__":
    sys.exit(main())
