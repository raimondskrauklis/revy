---
name: md-formatting
description: >-
  Write and fix markdown so it renders correctly in GitHub and exports cleanly
  to Word/PDF via Pandoc. Use when creating or editing .md docs, formatting
  tables/lists/headings, fixing collapsed lists in docx export, or before
  handoff documents under docs/ or internal_docs/.
---

# Markdown formatting

## When to use

- **Authoring** new specs, findings, plans under `docs/` or `internal_docs/`
- **Fixing** MD that breaks in Word (lists on one line, tables as plain text)
- **Before** export — pair with **`md-docx-export`** skill for `.docx`

**Canonical reference (if present):** repo `docs/**/MD_FORMATTING_PATTERN.md` — read when unsure; otherwise follow this skill.

## Repo file header (convention)

First line = relative path comment (stripped on docx export):

```markdown
# docs/ML/EXAMPLE.md

# Document Title
```

Python: `# backend/app/...` · TypeScript: `// frontend/src/...`

## Critical rules (export-breaking if wrong)

### 1. Blank lines are structural

**Always** one blank line before and after:

- Headings
- Lists (first item too — most common bug)
- Tables
- Block quotes
- `---` horizontal rules
- Paragraphs

**Wrong** (lists collapse in DOCX):

```markdown
Key points:
- One
- Two
```

**Correct:**

```markdown
Key points:

- One
- Two
```

### 2. Headings

- ATX only: `#`, `##`, `###` — **not** underline `===` / `---` under text
- Blank line before and after each heading
- Do not skip levels (e.g. `##` then `####`)

### 3. Lists

- Bullets: `- ` only — **not** `•`, not bare `*`
- Numbered: `1.`, `2.`, `3.` in source — **not** repeated `1.` on every line
- Nested: indent children with **4 spaces**

### 4. Tables

Pipe tables only, with header separator row:

```markdown
| Column A | Column B |
|:---|---:|
| left | 123 |
```

- Blank line **before and after** the table
- Single-line cell text only — no lists or code blocks inside cells
- Alignment: `:---` left, `:---:` center, `---:` right

### 5. Horizontal rules

`---` on its own line, blank lines around it — **not** `________`

### 6. Emphasis

- Bold: `**text**` — not Unicode bold
- Code: `` `identifier` `` · fenced blocks for commands/SQL

## Optional YAML front matter (Pandoc title page)

```yaml
---
title: "Document Title"
date: "May 2026"
---
```

Place at top **after** path comment only if you want a Word title page.

## Pre-export checklist

Copy when finishing a doc:

```
- [ ] Path comment line 1 (if handoff doc for Word export)
- [ ] ATX headings + blank lines around them
- [ ] Blank line before every list
- [ ] Pipe tables + |:---| row + blank lines around tables
- [ ] No underline headings, no • bullets, no ________ rules
- [ ] Heading hierarchy consistent (no skipped levels)
- [ ] Numbered lists use 1. 2. 3. in source
```

## Related skills

**Import Word → MD:** `docx-md-export` — then apply this checklist on the output.

```bash
.cursor/skills/docx-md-export/scripts/export_docx_to_md.sh path/to/doc.docx
```

**Export to compact Word (9pt, narrow margins):** `md-docx-export` — run only after this formatting passes the checklist.

```bash
.cursor/skills/md-docx-export/scripts/export_md_to_docx.sh path/to/doc.md
```

## Agent workflow

1. Apply rules above while writing/editing `.md`.
2. If user wants Word: run checklist → `md-docx-export`.
3. Do not grow root `docs/` with new `.md` unless user asked (see `.cursorrules`).
