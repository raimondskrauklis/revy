# docs/review-pipeline/pr-summary-rollup/waves/PR_SUMMARY_ROLLUP_P4_EXECUTION.md

# P4 — Lifetime readability + explain layer (execution)

Phase **P4** of [`PR_SUMMARY_ROLLUP_GENERAL_PLAN.md`](../PR_SUMMARY_ROLLUP_GENERAL_PLAN.md). Baseline: [`PR_SUMMARY_ROLLUP_P4_READABILITY_FINDINGS.md`](../PR_SUMMARY_ROLLUP_P4_READABILITY_FINDINGS.md). **P4 only.**

**Goal:** Authors can scan solved vs remaining on long PRs; verbose breakdown in `<details>` during dogfood — no rollup math changes.

**Peer review:** [pass 2](../reviews/execution-peer-review/pass-02-2026-08-09.md) — **BLOCK phase-execution: no** (splice fix in P4.1 first).

## Decisions locked for P4

- PSR-Q11–Q18 from readability findings (incl. splice boundary PSR-Q17, Moonshot stub PSR-Q18).
- Reuse `filter_snapshot` v1 keys only — no new manifest fields.
- Deterministic splice owns full P4 block; Moonshot must not emit scan table or `<details>` (extend system + user prompt).
- PSR-Q14 verbosity trim — **human gate** P4.4.
- `format_pr_rollup_check_one_liner` — **unchanged** in P4 (issue comment carries full story).

## Out of scope for P4

- Rollup compute / migration / API schema changes
- Listing hidden groups in `### Still open on PR` table
- Push-block rewrite (PSR-Q16: one-line cross-ref in `<details>` only)
- Check-run hidden breakdown
- LV i18n

---

## P4.0 — Splice boundary fix (prerequisite)

**What:** Add `_replace_pr_summary_section` (or retarget `splice_deterministic_pr_summary_block`) so PR summary replace ends at push/lifetime **section** boundaries (`**Since last push:**`, `### Resolution metrics`, `### Files needing attention`, `### This generation`) — **not** `\n<details>` inside the rollup block. `_SECTION_END_MARKERS` must not truncate inner `<details>`.

**Files:** `backend/app/services/github_publish_formatter.py`, `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py -k "splice_deterministic_pr_summary or pr_summary" -q
```

**Test:** `splice_deterministic_pr_summary_block` called **twice** on markdown that already contains P4 block with `<details>` — idempotent, no duplicate/truncated breakdown.

---

## P4.1 — Publishable status + scan table

**What:** Extend `format_pr_resolution_rollup_block()` — status line (PSR-Q13 qualified copy); compact markdown table (raised / resolved / display open / hidden when nonzero). Place PSR-Q9 `lifetime_disclosure` after table, before `<details>`. **Update** existing `test_format_pr_resolution_rollup_block_*` and related splice assertions for new layout.

**Files:** `backend/app/services/github_publish_formatter.py`, `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py -k "pr_resolution_rollup_block or pr_summary" -q
```

---

## P4.2 — `<details>` verbose breakdown

**What:** Append collapsed `<details><summary>Lifetime breakdown</summary>` with resolved-by-method bullets, hidden breakdown from `filter_snapshot`, guarded reconciliation (PSR-Q15), lifetime-rate footnote, push cross-ref when `still_open_prior ≠ still_open_display` (PSR-Q16).

**Reconciliation guard:** print `raised = resolved + display_open + hidden` only when equality holds; else use `raw_active_before_filters` and note addressed-pending actives.

**Files:** `backend/app/services/github_publish_formatter.py`, `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:** #501-shaped fixture (`raised=29`, `resolved=17`, `still_open_display=0`, full `filter_snapshot`).

---

## P4.3 — Moonshot / splice parity

**What:** Wire P4 block through fixed splice path; extend `ISSUE_COMMENT_FORMAT_SYSTEM_PROMPT` + user prompt — Moonshot emits minimal `### PR summary` stub only (no scan table, no `<details>`); deterministic splice owns full block (PSR-Q18). `_issue_comment_meets_product_bar` — still anchors on `### PR summary` heading only.

**Add** prompt/splice regression tests in `test_moonshot_review.py` and formatter tests (tests do not exist yet for `-k "pr_summary or splice"` on moonshot module).

**Files:** `backend/app/integrations/moonshot_review.py`, `backend/app/services/github_publish_formatter.py`, `backend/tests/unit/test_moonshot_review.py`, `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py tests/unit/test_moonshot_review.py -k "pr_summary or splice or moonshot" -q
```

---

## P4.4 — Staging spot-check + human gate

**What:** Publish on staging (#501-class long PR); operator expands `<details>` and confirms `29 = 17 + 0 + 12` without code. Record PSR-Q14 trim decision. Note in staging memo: check-run one-liner unchanged — optional author confusion if they only read check.

**Files:** `docs/review-pipeline/pr-summary-rollup/PR_SUMMARY_ROLLUP_STAGING_VALIDATION.md` (append P4 wave row)

**Human gate:** Operator marks P4 readability PASS or lists trim actions for P4.5.

**Not in scope:** dogfood script markdown-shape gate (optional follow-up).

---

## P4.5 — Doc sync (optional trim)

**What:** If PSR-Q14 resolved to trim defaults — implement; update README + execution index P4 Done + sha.

**Files:** `docs/review-pipeline/pr-summary-rollup/README.md`, `waves/PR_SUMMARY_ROLLUP_EXECUTION.md`

---

**Phase gate** (from `backend/`):

```bash
cd backend && pipenv run pytest tests/unit/test_github_pr_resolution_rollup.py tests/unit/test_github_publish_formatter.py tests/unit/test_moonshot_review.py -q
```

**Depends on:** P0–P3 on `main` + staging.

**LOOP order:** P4.0 → P4.1 → P4.2 → P4.3 → P4.4 → P4.5 (optional).

**Next:** `phase-execution` on `feat/psr-p4-readability` from `main`, starting **P4.0** ([pass-02](./reviews/execution-peer-review/pass-02-2026-08-09.md)).
