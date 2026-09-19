# docs/review-pipeline/resolution-honesty/RESOLUTION_HONESTY_P3_EXECUTION.md

# P3 — Lifetime rollup (execution)

Phase **P3** of [`RESOLUTION_HONESTY_GENERAL_PLAN.md`](./RESOLUTION_HONESTY_GENERAL_PLAN.md). Baseline: [`RESOLUTION_HONESTY_FINDINGS.md`](./RESOLUTION_HONESTY_FINDINGS.md) RH-Q2, RH-Q12. **P3 only.**

**Goal:** Scan table matches H4 and PSR-Q15. New PRs do not create file+category superseded, so raised is not emptied by rewrite.

## Decisions locked for P3

- Keep `raised_count = len(state != superseded)` in `build_pr_resolution_rollup`. P0 stopped **creating** those rows; historical superseded stay excluded (no remap of dogfood #1).
- `resolved_count` = those non-superseded groups with `state=resolved` (H2 or dismiss only).
- PSR-Q15: `raised == resolved + still_open_display + hidden_total`. Keep `_format_publishable_status_line` / details identity copy. Not a three-term equation. Orphan / `ever_inlined` matching is **`group.id`** from P0.4 — do not “fix raised math” here to paper over UUID/fingerprint mismatch.
- `path_removed` remains a **display bucket** in `resolved_by_method` via `_is_lifetime_path_removed_resolution` (method still `absent_and_addressed`).
- Title/severity rewrite on a **new** PR must not drop `raised_count` (no peer supersede).

## Out of scope for P3 (later phases)

- Comment scan layout / GH-Q9 → **P4**
- Remap of #1’s 13 superseded fingerprints → never in this program (RH-Q10)
- GitHub thread mutations → **P4**

---

## P3.1 — Raised does not shrink on rewrite

**What:** Unit test: two revisions, second run retitles leftover claims (P0 continuation / new fingerprint without supersede). `build_pr_resolution_rollup` `raised_count` stays the unique claims; `resolved_count` only H2/dismiss. Keep the `state != superseded` filter.

**Files:** `backend/app/services/github_pr_resolution_rollup.py`, `backend/tests/unit/test_github_pr_resolution_rollup.py`

**Deliverable:** rewrite fixture: raised does not fall to “this generation only”; resolved 0 if nothing H2-closed.

```bash
cd backend && pipenv run pytest tests/unit/test_github_pr_resolution_rollup.py -q
```

---

## P3.2 — H2 resolved + PSR-Q15 identity

**What:** Fixture: N unique claims, K H2-closed (`absent_and_addressed`), leftovers still active, optional hidden in `filter_snapshot`. Assert `raised == resolved + still_open_display + hidden_total`. `resolved_by_method.path_removed` increments only for path-gone hygiene, not for line-miss H2.

**Files:** `backend/tests/unit/test_github_pr_resolution_rollup.py`, `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_pr_resolution_rollup.py tests/unit/test_github_publish_formatter.py -q
```

---

## P3.3 — Historical superseded residual

**What:** Fixture with 13 `superseded` + 10 `active` (dogfood #1 shape). `raised_count == 10`, `resolved_count == 0`. Documents RH-Q10: this program does not resurrect those rows.

**Files:** `backend/tests/unit/test_github_pr_resolution_rollup.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_pr_resolution_rollup.py -k "superseded or raised" -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_pr_resolution_rollup.py tests/unit/test_github_publish_formatter.py -q
pipenv run ruff check app/services/github_pr_resolution_rollup.py
```

**Deploy:** no migration.

**Next:** [`RESOLUTION_HONESTY_P4_EXECUTION.md`](./RESOLUTION_HONESTY_P4_EXECUTION.md)
