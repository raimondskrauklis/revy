# Review engineering context P6 — Publish surface depth (execution)

Phase **P6** of [REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md](../REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md). Baseline: [REVIEW_ENGINEERING_CONTEXT_FINDINGS.md](../REVIEW_ENGINEERING_CONTEXT_FINDINGS.md) § Wave 2, RCX-13, RCX-G10, RCX-D13–D14. **P6 only.**

**Goal:** Greptile Summary parity on revybot **issue comment** — narrative + confidence rationale + structured `<details>` — not a thin table.

**Dogfood:** This phase is the **real PR** for RCX validation (RCX-D15, RCX-18) — must touch `backend/**`.

## Decisions locked for P6

- **Issue comment only** — `build_publish_format_result.check_summary` unchanged (G3 compact).
- **Fallback = product minimum** (RCX-D14) — Moonshot disabled/failed must match section depth; when Moonshot succeeds, output must include the same section list (P6.8).
- **Locked section order** (match Greptile on PR #60):
  1. `## Revy code review` header
  2. **Narrative** — 2–4 sentences: what changed, main risk theme, merge-readiness hint
  3. **Confidence score** — `N/5` plus **one sentence rationale** (why not higher/lower)
  4. **Since last push** — G9 resolution prose when present (existing)
  5. Resolution metrics block when present (existing)
  6. **Files needing attention** — bullet list with paths (existing)
  7. **Findings** — severity table `Severity | Category | Title | File` (existing)
  8. `<details>` **Security review** — when any **active** finding has `category=security`
  9. `<details>` **Important files changed** — table `File | Note` capped at `IMPORTANT_FILES_ROW_CAP` (default 8)
  10. `<details>` **Review metadata** — head_sha, revision, Revy link (existing)
  11. Index footer when `fallback_reason` or full index (existing)
- **No mermaid.** Moonshot path capped at **12000 chars** total; narrative target **2–4 sentences** (~80–200 words) — not a separate word budget that can exceed the char cap.
- **Narrative helpers** — deterministic templates in `github_publish_formatter.py`; Moonshot may rewrite when enabled.

## Out of scope for P6

- Check-run summary expansion
- Frontend
- `context_stats` API → **P7**
- Staging memo fill → **P8**

---

## P6.1 — Moonshot system prompt + prompt contract test

**What:**

1. Replace “short narrative” in `ISSUE_COMMENT_FORMAT_SYSTEM_PROMPT` with locked section list (narrative, confidence + rationale, G9, files, findings table, security `<details>`, important files `<details>`, metadata `<details>`).
2. Add test that **asserts prompt content** — e.g. `test_issue_comment_format_system_prompt_lists_required_sections` importing `ISSUE_COMMENT_FORMAT_SYSTEM_PROMPT` and checking `"short narrative"` absent and `"rationale"` / `"Security"` / `"Important files"` present; **or** assert `complete_issue_comment_markdown` passes `system_prompt=ISSUE_COMMENT_FORMAT_SYSTEM_PROMPT` via call kwargs inspection.

**Files:** `backend/app/integrations/moonshot_review.py`, `backend/tests/unit/test_moonshot_review.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_moonshot_review.py -k "issue_comment_format or complete_issue_comment" -q
```

---

## P6.2 — Confidence rationale (fallback + template)

**What:** Add `_confidence_rationale(groups) -> str` — one sentence from active severity counts. Insert after confidence line in fallback.

**Files:** `backend/app/services/github_publish_formatter.py`, `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py -k "confidence_rationale or fallback" -q
```

---

## P6.3 — Narrative paragraph (fallback)

**What:** Add `_review_narrative_paragraph(ctx) -> str` — 2–4 sentences from active findings. Place after header, before confidence block.

**Files:** `backend/app/services/github_publish_formatter.py`, `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py -k "narrative" -q
```

---

## P6.4 — Security `<details>` block

**What:** When any active group has `FindingCategory.security`, append collapsible security block (title + file per finding).

**Files:** `backend/app/services/github_publish_formatter.py`, `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py -k "security" -q
```

---

## P6.5 — Important files changed table

**What:** `<details><summary>Important files changed</summary>` — table from distinct active finding paths + title as note; cap rows.

**Files:** `backend/app/services/github_publish_formatter.py`, `backend/tests/unit/test_github_publish_formatter.py`

**Constant:** `IMPORTANT_FILES_ROW_CAP = 8` next to `SUMMARY_ROW_CAP`.

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py -k "important_files" -q
```

---

## P6.6 — Moonshot user prompt enrichment

**What:** Extend `build_pr_review_comment` user prompt — narrative hints, paths, severities, categories, titles; instruct model to use provided confidence + rationale template.

**Files:** `backend/app/services/github_publish_formatter.py`, `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py -k "build_pr_review_comment" -q
```

---

## P6.7 — Regression guard (fallback path)

**What:** Ensure JSON-wrapper / unparsed Moonshot still returns fallback; G9, resolution metrics, metadata footer unchanged.

**Files:** `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py -k "falls_back or moonshot_failure" -q
```

---

## P6.8 — Moonshot success-path shape (RCX-D14)

**What:** Async test `test_build_pr_review_comment_moonshot_success_includes_greptile_sections` — mock `complete_issue_comment_markdown` to return markdown with narrative, rationale, and at least one `<details>` block; assert `build_pr_review_comment` returns that text (not fallback) and contains `Confidence`, `rationale` or rationale sentence pattern, and `Review metadata`.

**Files:** `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py -k "moonshot_success_includes_greptile" -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run ruff check app/integrations/moonshot_review.py app/services/github_publish_formatter.py
pipenv run pytest tests/unit/test_github_publish_formatter.py tests/unit/test_moonshot_review.py -q
```

**Next:** [REVIEW_ENGINEERING_CONTEXT_P7_EXECUTION.md](./REVIEW_ENGINEERING_CONTEXT_P7_EXECUTION.md)
