---
name: md-docx-export
description: >-
  Format markdown for clean export and build compact Word (.docx) files with
  9pt body text, proportional headings, and narrow margins via Pandoc. Use when
  the user asks to create or export MD docs, generate docx, Word handoff,
  smaller font, narrow layout, or Pandoc export for stakeholder handoff documents.
---

# MD → compact DOCX export

## When to use

- Handoff `.md` specs to stakeholders who want **Word**
- Task/findings, investigation reports, planning docs under `docs/` or `internal_docs/`
- User asks for **smaller font (~9pt)**, **narrow page**, compact tables

**Not** for platform refactor docs unless the user asks — LU and internal specs are the usual targets.

## MD source rules

Use the **`md-formatting`** skill when **writing** MD.

This skill is **export + typography** only. Quick requirements:

- Path comment line 1 optional — stripped on export **only** if line 1 is `# path/to/file.md` (contains `/`)
- Lists/tables/headings must pass `md-formatting` checklist or DOCX will break

Do **not** create or update `.md` unless the user asked.

## Typography (reference.docx)

| Style | Size |
|:---|---:|
| Normal (body) | **9pt** Calibri |
| Heading 1 | 16pt |
| Heading 2 | 13pt |
| Heading 3 | 11pt |
| Heading 4 | 10pt |
| Heading 5–6 | 9pt |
| Page margins | **1.5 cm** all sides (narrow) |
| Line spacing | 1.15 |

Regenerate reference after changing sizes:

```bash
cd backend && pipenv run python ../.cursor/skills/md-docx-export/scripts/build_reference_docx.py
```

Output: `.cursor/skills/md-docx-export/assets/compact-reference.docx`

## Export workflow

**One or more files:**

```bash
chmod +x .cursor/skills/md-docx-export/scripts/export_md_to_docx.sh

.cursor/skills/md-docx-export/scripts/export_md_to_docx.sh \
  docs/programs/example/EXAMPLE_TASK.md \
  docs/programs/example/EXAMPLE_FINDINGS.md
```

**Pandoc path:** script uses `PANDOC` env, else `/tmp/pandoc-arm64/pandoc-3.6.4-arm64/bin/pandoc`, else `pandoc` on PATH.

**Output:** `same/path/file.docx` next to each `.md`.

## Agent checklist

1. Confirm MD passes **`md-formatting`** checklist (lists/tables/headings).
2. Ensure `compact-reference.docx` exists (run `build_reference_docx.py` if missing).
3. Run `export_md_to_docx.sh` with absolute or repo-relative paths.
4. Do **not** link handoff docs to unrelated platform docs unless user requests.

## PDF (optional)

For PDF with same narrow geometry, use reference PDF engine separately; default path is **docx** only.

## Round-trip pair

| Direction | Skill | Script |
|:---|:---|:---|
| MD → DOCX | `md-docx-export` | `export_md_to_docx.sh` |
| DOCX → MD | `docx-md-export` | `export_docx_to_md.sh` |
