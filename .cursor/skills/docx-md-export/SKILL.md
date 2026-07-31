---
name: docx-md-export
description: >-
  Convert Word (.docx) files to GitHub-flavored markdown via Pandoc with
  post-processing. Use when the user asks to import docx, convert Word to MD,
  reverse md-docx-export, or digitize Word handoffs under docs/ or
  internal_docs/.
---

# DOCX → MD export

## When to use

- Reverse of **`md-docx-export`**: Word handoff → editable `.md`
- Task specs, planning annexes, stakeholder docs under `internal_docs/` or `docs/`
- User asks to **convert**, **import**, or **digitize** a `.docx`

**Not** for platform code docs unless the user asks.

## Import workflow

**One or more files:**

```bash
chmod +x .cursor/skills/docx-md-export/scripts/export_docx_to_md.sh

.cursor/skills/docx-md-export/scripts/export_docx_to_md.sh \
  docs/programs/example/HANDOFF.docx
```

**Pandoc path:** script uses `PANDOC` env, else `/opt/homebrew/bin/pandoc`, else `/tmp/pandoc-arm64/pandoc-3.6.4-arm64/bin/pandoc`, else `pandoc` on PATH.

**Output:** `same/path/file.md` next to each `.docx`.

## What the script does

1. Pandoc: `docx` → `gfm` (pipe tables, ATX headings where Word used heading styles)
2. Post-process (`postprocess_md_from_docx.py`):
   - Repo path comment line 1 (`# docs/.../file.md` or `# internal_docs/.../file.md`)
   - Strip Pandoc attributes (`{.underline}`, etc.)
   - Remove empty `<!-- -->` list separators
   - Unescape `\"` → `"`
   - Remove trailing `\` hard line breaks

## After import

Word docs that use **bold Normal** instead of **Heading** styles stay as `**bold**` — not auto-fixed.

Run **`md-formatting`** checklist on the output:

- Blank lines before lists/tables/headings
- Pipe tables + `|:---|` row
- ATX headings where sections should be navigable
- Numbered lists: `1.` `2.` `3.` in source (not repeated `1.`)

Re-export to Word when done: **`md-docx-export`**.

## Agent checklist

1. Run `export_docx_to_md.sh` with repo-relative or absolute paths.
2. Skim output for grid tables, collapsed lists, or all-bold sections.
3. Apply **`md-formatting`** fixes if user wants clean GitHub/Word round-trip.
4. Do **not** create or update `.md` beyond the conversion unless the user asked.

## Round-trip pair

| Direction | Skill | Script |
|:---|:---|:---|
| MD → DOCX | `md-docx-export` | `export_md_to_docx.sh` |
| DOCX → MD | `docx-md-export` | `export_docx_to_md.sh` |
