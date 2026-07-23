#!/usr/bin/env bash
# .cursor/skills/docx-md-export/scripts/export_docx_to_md.sh
# Convert one or more .docx files to .md (GFM + KP post-processing).
set -euo pipefail

ROOT="$(cd "$(dirname "$0")/../../../.." && pwd)"
POSTPROCESS="$(dirname "$0")/postprocess_md_from_docx.py"
PANDOC="${PANDOC:-}"

if [[ -z "$PANDOC" ]]; then
  if [[ -x /opt/homebrew/bin/pandoc ]]; then
    PANDOC=/opt/homebrew/bin/pandoc
  elif [[ -x /tmp/pandoc-arm64/pandoc-3.6.4-arm64/bin/pandoc ]]; then
    PANDOC=/tmp/pandoc-arm64/pandoc-3.6.4-arm64/bin/pandoc
  elif command -v pandoc >/dev/null 2>&1; then
    PANDOC="$(command -v pandoc)"
  else
    echo "ERROR: pandoc not found. Set PANDOC= or install pandoc (brew install pandoc)." >&2
    exit 1
  fi
fi

if [[ $# -lt 1 ]]; then
  echo "Usage: $0 path/to/doc.docx [more.docx ...]" >&2
  exit 1
fi

for DOCX in "$@"; do
  if [[ ! -f "$DOCX" ]]; then
    echo "ERROR: not found: $DOCX" >&2
    exit 1
  fi
  OUT="${DOCX%.docx}.md"
  TMP="$(mktemp "${TMPDIR:-/tmp}/docx2md.XXXXXX")"
  trap 'rm -f "$TMP"' EXIT

  "$PANDOC" "$DOCX" --from=docx --to=gfm --wrap=none -o "$TMP"
  python3 "$POSTPROCESS" "$TMP" "$OUT" --root "$ROOT"
  rm -f "$TMP"
  trap - EXIT

  echo "Wrote $OUT"
done
