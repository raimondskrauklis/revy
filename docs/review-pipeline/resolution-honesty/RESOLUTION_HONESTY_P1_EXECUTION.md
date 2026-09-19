# docs/review-pipeline/resolution-honesty/RESOLUTION_HONESTY_P1_EXECUTION.md

# P1 — Honest closure (H2) (execution)

Phase **P1** of [`RESOLUTION_HONESTY_GENERAL_PLAN.md`](./RESOLUTION_HONESTY_GENERAL_PLAN.md). Baseline: [`RESOLUTION_HONESTY_FINDINGS.md`](./RESOLUTION_HONESTY_FINDINGS.md) RH-Q1, RH-Q7, RH-Q9. **P1 only.**

**Goal:** Close a group when compare/HEAD succeeded and the path is gone or this-run **findings** in that `file_path`+`category` are **zero**. Do not require Pass 1 `addressed`. Do not close leftovers while ≥ 1 finding remains in that file+category.

## Decisions locked for P1

- **Supersedes FR-Q3** / CS Option B. Method string stays `absent_and_addressed` (FR-Q13 reopen still keys that method).
- **Two counts (do not mix):** P0 **bind** uses unbound **groups** (merge iff exactly one). P1 **H2** uses this-run **findings** count in the same `file_path`+`category`.
- `should_close_absent_and_addressed` predicate: `state=active`, `closure_blocked_reason is None`, not bound this run, **and** (`path_gone` **or** `this_run_finding_count == 0`). Drop the `resolution_status == addressed` requirement.
- Bound this run = group id linked by P0 reconcile (`last_seen_revision_id` is the current revision).
- `this_run_finding_count` = number of **this-run findings** with the same `file_path` + `category`. Close when count == 0 (two same-file **fixes** both close). Skip H2 when count ≥ 1 (leftovers / unmatched). **Do not** use P0’s “≠ 1 groups” as the close predicate — that would refuse to close two same-file fixes.
- `path_gone` = Pass 1 hygiene already marked the path gone, or the file is absent at HEAD. Display bucket `path_removed` stays in rollup (`_is_lifetime_path_removed_resolution`); **no** new `ResolutionMethod` enum value.
- Pass 1 stays line-region (`patch_touches_line_region`). Do not treat whole-file touch as `addressed`.
- Compare/HEAD failure: keep `COMPARE_FAILED_REASON` / `HEAD_CHECK_FAILED_REASON` blocking close.
- FR-Q11 Pass 3 volume may drop for missed-line **fixes** that now H2-close. Do **not** also H2-close leftovers held by findings count ≥ 1.
- Home remains `apply_pass2_closure_for_review_run` in `github_finding_closure.py`.

## Out of scope for P1 (later phases)

- This-push manifest / N/A → **P2**
- Lifetime `raised_count` → **P3**
- Issue-comment copy / GH-Q9 → **P4**
- Dogfood PR → **P5**
- Widen Pass 1 region (RH-Q7)

---

## P1.1 — Closure predicate without `addressed`

**What:** Change `should_close_absent_and_addressed` to (`bound_this_run`, `this_run_finding_count`, `path_gone`, `closure_blocked_reason`). Remove `resolution_status` from the close decision. Close iff not bound and (`path_gone` or `this_run_finding_count == 0`). `this_run_finding_count == 2` (two leftovers still reported) → False. `this_run_finding_count == 0` (two same-file fixes, nothing left) → True. Update `should_reopen_absent_and_addressed` to key off bound-this-run / group identity, still requiring `resolution_method=absent_and_addressed`.

**Files:** `backend/app/services/github_finding_closure_rules.py`, `backend/tests/unit/test_github_finding_closure.py`

**Deliverable:** `still_open` + unbound + compare ok + finding count 0 → close; finding count ≥ 1 → stay open; `addressed` is not required; `compare_failed` does not close.

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_closure.py -k "should_close_absent_and_addressed or should_reopen" -q
```

---

## P1.2 — Pass 2 uses this-run finding counts

**What:** In `apply_pass2_closure_for_review_run`, replace `fingerprint_in_current_run` with bound group ids from this run. For each remaining active group, compute `this_run_finding_count` (findings in this run with that `file_path`+`category`) and `path_gone`. Close only if `path_gone` or count == 0; skip if count ≥ 1. Wire the same inputs at every `should_close_absent_and_addressed` call site (`github_publish.py`).

**Files:** `backend/app/services/github_finding_closure.py`, `backend/app/services/github_publish.py`, `backend/tests/unit/test_github_finding_closure.py`

**Deliverable:** two same-file fixes (PAT + innerHTML-class, zero findings left in that file+category) both `resolved`; two same-file leftovers stay `still_open`; SELECT line-miss with zero leftover findings in that file+category closes.

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_closure.py -q
```

---

## P1.3 — Ambiguous-continuation + eval-insert tests

**What:** Unit tests: (1) line insert above `eval` — P0 continuation already bound → Pass 2 does not close; (2) two leftover same-category claims in one file (findings count ≥ 1) → neither H2-closed; (3) zero this-run findings in that file+category → both gone claims resolve with method `absent_and_addressed`; (4) path gone → close with method `absent_and_addressed` (`path_removed` **bucket** is P3.2).

**Files:** `backend/tests/unit/test_github_finding_closure.py`, `backend/tests/unit/test_github_finding_reconcile.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_closure.py tests/unit/test_github_finding_reconcile.py -q
```

---

## P1.4 — Pass 1 line-region unchanged

**What:** Confirm `apply_resolution_status_for_synchronize` / `patch_touches_line_region` still exact-region. Add a regression test that a hunk elsewhere in the same file does **not** stamp `addressed`. Leave production `patch_touches_line_region` unchanged.

**Files:** `backend/app/services/github_resolution_metrics.py`, `backend/tests/unit/test_github_resolution_metrics.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_resolution_metrics.py -k "patch_touches_line_region" -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_finding_closure.py tests/unit/test_github_finding_reconcile.py tests/unit/test_github_resolution_metrics.py -q
pipenv run ruff check app/services/github_finding_closure_rules.py app/services/github_finding_closure.py app/services/github_publish.py app/services/github_resolution_metrics.py
```

**Deploy:** no migration. Ship after `0035` (P0) is applied.

**Next:** [`RESOLUTION_HONESTY_P2_EXECUTION.md`](./RESOLUTION_HONESTY_P2_EXECUTION.md)
