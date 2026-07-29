# docs/review-pipeline/finding-resolution/waves/FINDING_RESOLUTION_CLOSURE_SCOPE_C1_EXECUTION.md

# C1 — HEAD hygiene pipeline (execution)

Phase **C1** of [FINDING_RESOLUTION_CLOSURE_SCOPE_GENERAL_PLAN.md](../FINDING_RESOLUTION_CLOSURE_SCOPE_GENERAL_PLAN.md). Baseline: findings § Architecture + CS-Q7. **C1 only** (manifest → C2).

**Goal:** Pass 1b HEAD path-gone hygiene + Pass 2 widen; aged cohort closes E2E.

## Decisions locked for C1

- Hygiene signal: `path_absent_at_head` → Contents API 404 at `revision.head_sha`; `None` = fail closed (R4).
- Pass 1b: all **active** groups on PR; skip paths in `renamed_from_paths` (CS-Q8).
- Pass 1a: pairing cohort unchanged (`patch_touches_line_region` + push-pair `removed_paths`).
- Pass 2: SQL `OR` pairing cohort **OR** `resolution_status == addressed`; rules unchanged.
- Compare-first: never `return 0` before compare/HEAD checks when prior publish exists.
- Same reconcile run: stamp + Pass 2 close in one pipeline (R2 mitigation).

## Out of scope for C1

- `build_resolution_pass_manifest` rate exclusion → **C2**
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

**What:** New module `github_path_hygiene.py`: `path_absent_at_head(...) -> bool | None` using `fetch_repository_file_at_ref`; `paths_absent_at_head` batch for unique active `file_path` values.

**Files:** `backend/app/services/github_path_hygiene.py`, `backend/tests/unit/test_github_path_hygiene.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_path_hygiene.py -q
```

---

## C1.3 — Compare-first + Pass 1b stamp

**What:** Refactor `apply_resolution_status_for_synchronize`: fetch compare first; Pass 1a on pairing cohort; Pass 1b on all active groups where path absent at HEAD and not rename-only guard.

**Files:** `backend/app/services/github_resolution_metrics.py`, `backend/tests/unit/test_github_resolution_metrics.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_resolution_metrics.py -q -k "synchronize or removed or hygiene or aged or empty_cohort"
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

**What:** Integration test: rev1 group `last_seen` outside rev3 pairing → sync stamps `addressed` → Pass 2 → `absent_and_addressed`. Add-then-delete uses HEAD 404 without compare removal. Rename: old path in `renamed_from_paths` → no hygiene stamp.

**Files:** `backend/tests/unit/test_github_resolution_metrics.py`, `backend/tests/unit/test_github_finding_closure.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_resolution_metrics.py tests/unit/test_github_finding_closure.py -q -k "aged or add_then_delete or rename_hygiene or e2e"
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint
pipenv run pytest tests/unit/test_github_api.py tests/unit/test_github_compare_patches.py tests/unit/test_github_path_hygiene.py tests/unit/test_github_resolution_metrics.py tests/unit/test_github_finding_closure.py -q
```

**Deploy:** ship with C2 before staging C3.

**Next:** [`FINDING_RESOLUTION_CLOSURE_SCOPE_C2_EXECUTION.md`](./FINDING_RESOLUTION_CLOSURE_SCOPE_C2_EXECUTION.md)
