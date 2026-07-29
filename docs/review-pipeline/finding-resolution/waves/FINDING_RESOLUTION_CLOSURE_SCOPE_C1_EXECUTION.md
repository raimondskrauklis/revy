# docs/review-pipeline/finding-resolution/waves/FINDING_RESOLUTION_CLOSURE_SCOPE_C1_EXECUTION.md

# C1 — HEAD hygiene pipeline (execution)

Phase **C1** of [FINDING_RESOLUTION_CLOSURE_SCOPE_GENERAL_PLAN.md](../FINDING_RESOLUTION_CLOSURE_SCOPE_GENERAL_PLAN.md). Baseline: findings § Architecture + CS-Q7 + R4. **C1 only** (manifest → C2).

**Goal:** Pass 1b HEAD path-gone hygiene + Pass 2 widen; aged cohort closes E2E.

## Decisions locked for C1

- Hygiene signal: **primary** = Contents API 404 at `revision.head_sha` via `fetch_repository_file_at_sha`; **fast path** = `file_path ∈ deleted_paths` (push-pair compare) when not in `renamed_from_paths` — still run HEAD check for add-then-delete when fast path misses.
- `path_absent_at_head` → `True` / `False` / `None`; **`None` = fail closed (R4):** no hygiene stamp; set `closure_blocked_reason = COMPARE_FAILED_REASON` (reuse existing constant); group stays `still_open`.
- Pass 1b: all **active** groups on PR; skip paths in `renamed_from_paths` (CS-Q8).
- Pass 1a: pairing cohort unchanged (`patch_touches_line_region` + push-pair `removed_paths`).
- Pass 2: SQL `OR` pairing cohort **OR** `resolution_status == addressed`; rules unchanged.
- Compare-first: never `return 0` before compare/HEAD checks when prior publish exists.
- Same reconcile run: stamp + Pass 2 close in one pipeline (R2 mitigation — superseded-publish E2E deferred to C3 operator note).

## Out of scope for C1

- `build_resolution_pass_manifest` rate exclusion + `head_check_failed_count` → **C2**
- Pass 3 cohort widen → FR-CS4
- Migration / `path_removed_at_revision_id` column

---

## C1.1 — Compare result: deleted vs renamed split

**What:** Add `deleted_paths` and `renamed_from_paths` to `ComparePatchesResult`; populate from `CompareCommitsResult` in `github_api.py`. Keep `removed_paths` as union for Pass 1a backward compat.

**Files:** `backend/app/integrations/github_api.py`, `backend/app/services/github_compare_patches.py`, `backend/tests/unit/test_github_api.py`, `backend/tests/unit/test_github_compare_patches.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_api.py tests/unit/test_github_compare_patches.py -q
```

---

## C1.2 — HEAD path-absent helper

**What:** New module `github_path_hygiene.py`: `path_absent_at_head(...) -> bool | None` using **`fetch_repository_file_at_sha`** (`github_api.py` — 404 → `NotFoundError` → `True`); `paths_absent_at_head` batch for unique active `file_path` values. Apply `deleted_paths` fast path per decisions above.

**Files:** `backend/app/services/github_path_hygiene.py`, `backend/tests/unit/test_github_path_hygiene.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_path_hygiene.py -q
```

---

## C1.3 — Compare-first + Pass 1b stamp + R4 fail-closed

**What:** Refactor `apply_resolution_status_for_synchronize`: fetch compare first; Pass 1a on pairing cohort; Pass 1b on all active groups where path absent at HEAD (hygiene helper) and not rename guard. On `path_absent_at_head is None` for a group's path: set `closure_blocked_reason = COMPARE_FAILED_REASON`, `resolution_status = still_open`, **no** hygiene stamp.

**Files:** `backend/app/services/github_resolution_metrics.py`, `backend/tests/unit/test_github_resolution_metrics.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_resolution_metrics.py -q -k "synchronize or removed or hygiene or aged or empty_cohort or head_fail"
```

---

## C1.4 — Pass 2 candidate widen

**What:** `apply_pass2_closure_for_review_run`: widen query with `or_(last_seen in pairing, resolution_status == addressed)`.

**Files:** `backend/app/services/github_finding_closure.py`, `backend/tests/unit/test_github_finding_closure.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_closure.py -q -k "pass2"
```

---

## C1.5 — E2E aged cohort + add-then-delete + rename guard

**What:** Integration test: rev1 group `last_seen` outside rev3 pairing → sync stamps `addressed` → Pass 2 → `absent_and_addressed`. Add-then-delete uses HEAD 404 without base→head compare removal. Rename: old path in `renamed_from_paths` → no hygiene stamp.

**Files:** `backend/tests/unit/test_github_resolution_metrics.py`, `backend/tests/unit/test_github_finding_closure.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_resolution_metrics.py tests/unit/test_github_finding_closure.py -q -k "aged or add_then_delete or rename_hygiene or e2e"
```

---

## C1.6 — R4 + FR-Q13 regression tests

**What:** Unit tests: HEAD API error → `closure_blocked_reason` set, no hygiene close. FR-Q13: re-report same fingerprint re-opens `absent_and_addressed` group (existing rules). Document R2 same-run close in test docstring; full superseded-publish scenario → **C3** operator checklist.

**Files:** `backend/tests/unit/test_github_resolution_metrics.py`, `backend/tests/unit/test_github_finding_closure.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_resolution_metrics.py tests/unit/test_github_finding_closure.py -q -k "head_fail or head_check or reopen or fr_q13"
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint
pipenv run pytest tests/unit/test_github_api.py tests/unit/test_github_compare_patches.py tests/unit/test_github_path_hygiene.py tests/unit/test_github_resolution_metrics.py tests/unit/test_github_finding_closure.py -q
```

**Deploy:** ship with C2 before staging C3.

**Next:** [`FINDING_RESOLUTION_CLOSURE_SCOPE_C2_EXECUTION.md`](./FINDING_RESOLUTION_CLOSURE_SCOPE_C2_EXECUTION.md)
