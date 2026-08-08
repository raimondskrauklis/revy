# docs/review-pipeline/pr-summary-rollup/waves/PR_SUMMARY_ROLLUP_P1_EXECUTION.md

# P1 — Formatter surfaces (GitHub comment + check) (execution)

Phase **P1** of [`PR_SUMMARY_ROLLUP_GENERAL_PLAN.md`](../PR_SUMMARY_ROLLUP_GENERAL_PLAN.md). Baseline: [`PR_SUMMARY_ROLLUP_FINDINGS.md`](../PR_SUMMARY_ROLLUP_FINDINGS.md) §catalog, PSR-Q7/Q9. **P1 only.**

**Goal:** User-visible two-horizon layout on GitHub issue comment and check run; formatter reads persisted rollup from P0.

## Decisions locked for P1

- Issue comment section order (top → bottom): narrative/merge/confidence → **`### PR summary` (lifetime)** → `**Since last push:**` (G9) → `### Resolution metrics (this push)` → files → two-block tables → details → **Review metadata** footer.
- `format_pr_resolution_rollup_block(rollup)` — EN-only markdown table: raised, resolved (with method breakdown), still open (display), lifetime rate `(lifetime)` label; append `lifetime_disclosure` when non-null (PSR-Q9).
- `splice_deterministic_pr_summary_block(markdown, rollup_block)` — insert/replace between narrative and G9; Moonshot path hooks here in P2.
- `build_check_run_summary` — add one-line PR rollup + one-line push delta after confidence line (compact parity).
- `_build_summary_json` — include `pr_resolution_rollup` key on display paths (parity with persisted manifest).
- Review metadata footer: `Reviews on this PR: {review_count}` · `Revision: {revision_number}` · `Head: {short_sha}` on issue comment only.
- PSR-Q8 spike (this phase): document publish-job routes returning `GitHubPublishJobResponse` in `waves/PSR_Q8_ROUTES_AUDIT.md` — ship field in P2.

## Out of scope for P1 (later phases)

- `GitHubPublishJobResponse.pr_resolution_rollup` schema + route tests → **P2**
- Moonshot system/user prompt updates → **P2**
- Dogfood script rollup gates → **P2**
- Staging sign-off → **P3**

---

## P1.1 — `format_pr_resolution_rollup_block`

**What:** Render lifetime block from manifest dict; explicit `(lifetime)` heading; method breakdown lines; N/A rate when denominator zero; PSR-Q9 disclosure footer appended when `lifetime_disclosure` set.

**Files:** `backend/app/services/github_publish_formatter.py`, `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py -k "pr_resolution_rollup_block or pr_summary" -q
```

---

## P1.2 — Fallback comment section order

**What:** Update `build_pr_review_comment_fallback` — insert `format_pr_resolution_rollup_block` from ctx/job rollup **before** G9 prose and resolution metrics block. Greptile-shape tests updated for new heading order.

**Files:** `backend/app/services/github_publish_formatter.py`, `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py -k "fallback" -q
```

---

## P1.3 — `splice_deterministic_pr_summary_block` + collapse refresh

**What:** Add splice helper (pattern: `splice_deterministic_findings_tables`); call from `apply_publish_summary_thread_collapse` and Moonshot refresh path stub (deterministic block when rollup present). `_insert_resolution_metrics_block` markers unchanged — PR summary sits above G9.

**Files:** `backend/app/services/github_publish_formatter.py`, `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py -k "splice_pr_summary or thread_collapse" -q
```

---

## P1.4 — Check-run one-liners + `_build_summary_json` parity

**What:** Extend `build_check_run_summary` with compact PR rollup + push delta lines. Ensure `_build_summary_json` copies `pr_resolution_rollup` from ctx/persisted manifest when building display snapshot.

**Files:** `backend/app/services/github_publish_formatter.py`, `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py -k "check_run_summary or summary_json" -q
```

---

## P1.5 — Review metadata footer + PSR-Q8 routes audit

**What:** Append review metadata footer to issue comment fallback + splice path. Write `waves/PSR_Q8_ROUTES_AUDIT.md` listing `installation_review.py` publish-job GET routes and confirming P2 adds `pr_resolution_rollup` to `GitHubPublishJobResponse`.

**Files:** `backend/app/services/github_publish_formatter.py`, `backend/tests/unit/test_github_publish_formatter.py`, `docs/review-pipeline/pr-summary-rollup/waves/PSR_Q8_ROUTES_AUDIT.md`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py -k "review_metadata or footer" -q
test -f docs/review-pipeline/pr-summary-rollup/waves/PSR_Q8_ROUTES_AUDIT.md
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_publish_formatter.py -q
pipenv run ruff check app/services/github_publish_formatter.py
```

**Next:** [`PR_SUMMARY_ROLLUP_P2_EXECUTION.md`](./PR_SUMMARY_ROLLUP_P2_EXECUTION.md)
