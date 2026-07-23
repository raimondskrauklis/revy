#!/usr/bin/env bash
# .cursor/skills/md-docx-export/scripts/export_md_to_docx.sh
# Export one or more .md files to compact .docx (9pt body, narrow margins).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
SKILL_ASSETS="$(dirname "$0")/../assets"
REF_DOC="${SKILL_ASSETS}/kp-compact-reference.docx"
PANDOC="${PANDOC:-}"

if [[ -z "$PANDOC" ]]; then
  if [[ -x /tmp/pandoc-arm64/pandoc-3.6.4-arm64/bin/pandoc ]]; then
    PANDOC=/tmp/pandoc-arm64/pandoc-3.6.4-arm64/bin/pandoc
  elif command -v pandoc >/dev/null 2>&1; then
    PANDOC="$(command -v pandoc)"
  else
    echo "ERROR: pandoc not found. Set PANDOC= or install pandoc." >&2
    exit 1
  fi
fi

if [[ ! -f "$REF_DOC" ]]; then
  echo "Building reference docx..." >&2
  (cd "$ROOT/backend" && pipenv run python "$ROOT/.cursor/skills/md-docx-export/scripts/build_reference_docx.py")
fi

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 path/to/doc.md [more.md ...]" >&2
  exit 1
fi

for MD in "$@"; do
  if [[ ! -f "$MD" ]]; then
    echo "ERROR: not found: $MD" >&2
    exit 1
  fi
  OUT="${MD%.md}.docx"
  # Skip KP path comment on line 1 only (# docs/.../file.md), not the title
  first_line=$(head -n 1 "$MD")
  if [[ "$first_line" =~ ^#[[:space:]].+\.md$ ]] && [[ "$first_line" == */* ]]; then
    "$PANDOC" --from=markdown --to=docx --reference-doc="$REF_DOC" -o "$OUT" < <(tail -n +2 "$MD")
  else
    "$PANDOC" "$MD" --from=markdown --to=docx --reference-doc="$REF_DOC" -o "$OUT"
  fi
  echo "Wrote $OUT"
done
