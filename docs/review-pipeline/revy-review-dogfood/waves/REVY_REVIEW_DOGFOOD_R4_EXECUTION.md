# docs/review-pipeline/revy-review-dogfood/waves/REVY_REVIEW_DOGFOOD_R4_EXECUTION.md

# R4 — HEAD contradiction suppression + inline 422 (execution)

Phase **R4** of [REVY_REVIEW_DOGFOOD_GENERAL_PLAN.md](../REVY_REVIEW_DOGFOOD_GENERAL_PLAN.md). Baseline: [REVY_REVIEW_DOGFOOD_FINDINGS.md](../REVY_REVIEW_DOGFOOD_FINDINGS.md) § RR-DG6, RR-DG2, RC-4. **R4 only.**

**Goal:** Re-run on fixed HEAD suppresses operator-matrix false positives (RR-V5: 0/5 on items 1, 2, 3, 15, 17); inline 422 does not drop publish silently.

## Decisions locked for R4

- **Insertion point:** `suppress_head_contradictions` runs at end of **reconcile** (`github_finding_reconcile.py`) before publish job build — groups marked `suppressed` / `state=resolved` with `resolution_method` head-contradiction; publish pipeline excludes them from active inline set. Do not filter only in publish flush (too late for manifest counts).
- Suppression uses **HEAD file content already fetched** in reconcile context — no new Contents API surface.
- Contradiction rules (minimum for RR-V5 fixtures):

| Matrix row | Rule sketch |
|------------|-------------|
| 1 — missing `or_` import | Claim missing symbol → HEAD line contains `or_` in sqlalchemy import |
| 2 — SystemStatusBar required props | Claim required props → HEAD shows only optional `connectionId?` / `compact?` |
| 3 — KPI skeleton count | Claim wrong count → HEAD contains `OVERVIEW_KPI_COUNT = 4` |
| 15 — export label misleading | Claim always wrong label → HEAD shows conditional Export List / Export Selected |
| 17 — prop migration | Claim missing props on callers → HEAD callers pass only optional props |

- Inline 422: retry nearest line once; on second failure publish issue-comment fallback; manifest `inline_publish_422_recovered_count`.

## Out of scope for R4

- Judge / Moonshot prompt changes
- Staging sign-off → **R5**

**Depends on:** R1 (pipeline completes). R3 preferred so resolution stamps align; suppression is independent and may commit after R1 if reconcile hook has no R3 coupling.

---

## R4.1 — HEAD contradiction suppression hook (reconcile)

**What:** Add `suppress_head_contradictions(session, groups, head_file_snippets)` called from reconcile completion path. Set `finding_suppressed_head_contradiction` log per fingerprint; manifest field `head_contradiction_suppressed_count`. Pluggable matchers for rules table above.

**Files:** `backend/app/services/github_finding_reconcile.py`, new `backend/app/services/github_finding_head_suppression.py`

**Deliverable:** Hook invoked once per reconcile run when active groups exist; suppressed groups excluded from publish inline build.

---

## R4.2 — RR-V5 matrix fixture tests

**What:** Parametrized unit tests for matrix rows 1, 2, 3, 15, 17 — input: finding title/message + HEAD file snippet from `misc/SUPER_ADMIN_DASHBOARD_STAGING_VALIDATION.md` → expect suppressed.

**Files:** `backend/tests/unit/test_github_finding_head_suppression.py` (new)

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_head_suppression.py -q
```

---

## R4.3 — Inline 422 recovery (RR-DG2)

**What:** On GitHub 422 for inline comment: attempt nearest-line retry once; on second failure, publish as issue-comment body entry for that group; increment `inline_publish_422_recovered_count` in `summary_json`.

**Files:** `backend/app/services/github_publish.py` (~1443–1454)

**Deliverable:** Unit test mocks 422 then success on retry; second test mocks double 422 → issue-comment fallback + manifest count.

---

**Phase gate:**

```bash
cd backend && pipenv run pytest \
  tests/unit/test_github_finding_head_suppression.py \
  tests/unit/test_github_publish.py -q -k "suppression or head_suppression or inline_422"
pipenv run ruff check app/services/github_finding_reconcile.py app/services/github_finding_head_suppression.py app/services/github_publish.py
```

**Next:** [REVY_REVIEW_DOGFOOD_R5_EXECUTION.md](./REVY_REVIEW_DOGFOOD_R5_EXECUTION.md)
