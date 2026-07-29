# Publish summary alignment P0 — Product contract + fallback (execution)

Phase **P0** of [PUBLISH_SUMMARY_ALIGNMENT_GENERAL_PLAN.md](../PUBLISH_SUMMARY_ALIGNMENT_GENERAL_PLAN.md). **P0 only.**

**Goal:** Deterministic issue comment and check share two-block findings; all verdict copy PR-wide.

**Peer review:** Architecture peer review (2026-07-29) gaps #1–#8 incorporated below.

## Decisions locked for P0

- `verdict_groups(ctx)` → `ctx.pr_active_groups if ctx.pr_active_groups is not None else ctx.groups`.
- Issue comment findings: `format_summary_comment(generation_groups=ctx.groups, pr_active_groups=verdict_groups(ctx))` — **no** `### Findings` section.
- **PSA-D10:** Flat two-block tables only — **drop** generation-only info `<details>` collapse (`_split_priority_and_info` / `_info_findings_collapsed_lines` path removed from fallback). Matches check run; update `greptile_shape` + `collapses_info` tests.
- **Verdict wiring (all use `verdict_groups(ctx)`):** `compute_confidence`, `_merge_recommendation`, `_confidence_rationale`, `_files_needing_attention`, `_security_details_lines`, `_important_files_details_lines`, `_review_narrative_paragraph` (PR-wide active count in lead).
- `build_check_run_summary`: confidence from `verdict_groups(ctx)`.
- **PSA-D11 — `summary_json`:** `confidence` + `active_count` from `verdict_groups(ctx)`; add `generation_active_count` (from `ctx.groups`) + `pr_active_count` (from `verdict_groups`).
- G9 + `_resolution_metrics_block` stay on `ctx.groups` only (PSA-D3).
- **`_insert_resolution_metrics_block` markers:** replace `### Findings` with `### This generation` / `### Still open on PR` (before files/details).
- **PSA-D12:** `compute_check_conclusion(groups)` unchanged — generation-scoped; out of scope (see findings).
- Flip `test_build_pr_review_comment_fallback_generation_only_not_pr_block` → `test_build_pr_review_comment_fallback_two_block_when_pr_active_extra`.

## PR review context (first commit)

- **Greptile:** `.greptile/files.json` — add `docs/review-pipeline/publish-summary-alignment/**`, `backend/app/services/github_publish_formatter.py`
- **Bugbot:** `.cursor/BUGBOT.md` — link to program README + findings

## Out of scope for P0

- Moonshot prompt / system prompt / product bar (P1)
- Staging memo (P2)
- `compute_check_conclusion` generation scope (PSA-D12)

---

## P0.1 — `verdict_groups` helper + module contract

**What:** Add helper and module-level docstring describing two-channel surface contract (PSA-D1–D4, PSA-D12).

**Files:** `backend/app/services/github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run ruff check app/services/github_publish_formatter.py
```

---

## P0.2 — Fallback two-block + flat tables (PSA-D10)

**What:** Refactor `build_pr_review_comment_fallback` — embed `format_summary_comment` after resolution metrics; remove `### Findings` path and info-collapse `<details>` branch. Update `test_build_pr_review_comment_fallback_greptile_shape` and `test_build_pr_review_comment_fallback_collapses_info_when_priority_exists` to expect two-block headings (info rows in block 1 table when in generation set).

**Files:** `backend/app/services/github_publish_formatter.py`, `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py -k "fallback_greptile or collapses_info or two_block" -q
```

---

## P0.3 — PR-wide verdict + rationale + `summary_json`

**What:** Wire `verdict_groups(ctx)` into confidence, merge, **`_confidence_rationale`**, files needing attention, security/important-files, narrative; `build_check_run_summary` confidence; `build_publish_format_result` / `_async` `summary_json` per PSA-D11. Add **`test_merge_recommendation_uses_pr_active_when_generation_clean`** (prior error-only in `pr_active_groups`, empty generation active → not “ready to merge”; confidence ≤3; rationale mentions remaining findings). Add **`test_confidence_rationale_pr_wide_when_generation_clean`**.

**Files:** `backend/app/services/github_publish_formatter.py`, `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py -k "confidence or merge or rationale or publish_format_result" -q
```

---

## P0.4 — Resolution metrics insert markers

**What:** Update `_insert_resolution_metrics_block` / `_append_resolution_metrics_block` marker list: `### This generation`, `### Still open on PR` (keep `### Files needing attention`, `<details>`). Update `test_insert_resolution_metrics_block_before_findings_section` → insert before `### This generation`.

**Files:** `backend/app/services/github_publish_formatter.py`, `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py -k "insert_resolution_metrics" -q
```

---

## P0.5 — Generation-only regression flip + parity prep

**What:** Replace `test_build_pr_review_comment_fallback_generation_only_not_pr_block` with two-block assertion (`### Still open on PR`, prior file path). Optional helper `_extract_summary_blocks_section` for P1 parity test (same substring from check vs issue).

**Files:** `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py -k "two_block" -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_publish_formatter.py -q
pipenv run ruff check app/services/github_publish_formatter.py
```

**Next:** [PUBLISH_SUMMARY_ALIGNMENT_P1_EXECUTION.md](./PUBLISH_SUMMARY_ALIGNMENT_P1_EXECUTION.md)
