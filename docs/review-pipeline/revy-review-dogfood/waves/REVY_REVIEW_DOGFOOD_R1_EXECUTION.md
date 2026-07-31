# docs/review-pipeline/revy-review-dogfood/waves/REVY_REVIEW_DOGFOOD_R1_EXECUTION.md

# R1 — Revision ingest idempotency (execution)

Phase **R1** of [REVY_REVIEW_DOGFOOD_GENERAL_PLAN.md](../REVY_REVIEW_DOGFOOD_GENERAL_PLAN.md). Baseline: [REVY_REVIEW_DOGFOOD_FINDINGS.md](../REVY_REVIEW_DOGFOOD_FINDINGS.md) § RR-DG3, RR-DG11, RC-1. **R1 only.**

**Goal:** Concurrent `synchronize` webhooks never abort on `uq_github_pr_revisions_pr_number`; one logical revision per `head_sha`.

## Decisions locked for R1

- Pre-check `_get_revision_for_head_sha` before `_append_revision` when `head_sha` is new on synchronize path.
- **Same `head_sha` as PR head:** keep current webhook semantics — return `(existing, None)` so pipeline does **not** re-trigger (duplicate delivery idempotency).
- On `IntegrityError` for `(pull_request_id, revision_number)`:
  1. Re-fetch revision by `(pull_request_id, head_sha)` — if found, return it (`github_revision_append_deduped`, reason `same_head_sha`).
  2. Else another worker won the `revision_number` with a **different** `head_sha` — `session.refresh(pull_request)`, retry `_append_revision` **once** with updated `revision_count`.
- Refactor `_append_revision`: increment `revision_count` only after successful insert (or use nested transaction so failed flush does not leave inflated count).
- Implement RR-Q5 outcome from R0 only (no extra migration scope).
- **Branch:** `feat/revy-review-dogfood-rr-w1`.

## PR review context (first code commit)

- **SSOT:** `.revy/review-context.json` — `active_program: revy-review-dogfood`; one `programs[]` entry; scope `backend/**`; three doc paths (execution index, findings, general plan).
- **Greptile:** `cd backend && pipenv run python -m scripts.generate_greptile_files_from_review_context --write`
- **Bugbot:** `.cursor/BUGBOT.md` — RR-W1 doc links

## Out of scope for R1

- Thread resolve → **R2**
- Resolution stamp → **R3**
- Optional `SELECT … FOR UPDATE` on PR row only if R1.4 concurrent tests fail without it

---

## R1.0 — Program PR review context

**What:** SSOT + Greptile + Bugbot for RR-W1. Update `test_parse_committed_ssot_file` for `active_program: revy-review-dogfood`.

**Files:** `.revy/review-context.json`, `.greptile/files.json`, `.cursor/BUGBOT.md`, `backend/tests/unit/test_engineering_context_manifest.py`

**Deliverable:**

```bash
cd backend && pipenv run python -m scripts.generate_greptile_files_from_review_context --check
pipenv run pytest tests/unit/test_generate_greptile_files.py tests/unit/test_engineering_context_manifest.py -q
```

---

## R1.1 — head_sha pre-check before append

**What:** In `_upsert_pull_request` synchronize path when `create_revision` and `fields["head_sha"] != existing.head_sha`: call `_get_revision_for_head_sha` first; return existing revision row when found (idempotent retry of same new SHA). When `fields["head_sha"] == existing.head_sha`, keep returning `(existing, None)` — no new revision, no pipeline re-run.

**Files:** `backend/app/services/github_pull_requests.py`

**Deliverable:** Unit tests pass:

- `test_synchronize_same_sha_skips_revision` (existing — still returns `None` revision)
- `test_synchronize_returns_existing_revision_when_head_sha_row_exists` (new — dedupe before append)

---

## R1.2 — IntegrityError recovery on revision_number collision

**What:** Catch `IntegrityError` on `uq_github_pr_revisions_pr_number` around revision insert. Recovery path per locked decisions (same-SHA dedupe, else refresh + single retry). Log `github_revision_append_deduped` at INFO with `reason` (`same_head_sha` | `revision_number_retry`). Ensure `revision_count` matches row count after failed append.

**Files:** `backend/app/services/github_pull_requests.py`

**Deliverable:** Unit tests pass:

- `test_append_revision_recovers_same_head_sha_after_unique_violation`
- `test_append_revision_retries_next_revision_number_after_different_sha_collision` (TenderPro `d915b4e` + `999ad17` scenario)

---

## R1.3 — RR-Q5 migration (only if R0 locked B)

**What:** Hand-written Alembic revision: unique index on `(pull_request_id, head_sha)` where `head_sha` not null; handle duplicate cleanup in migration if staging has dupes.

**Files:** `backend/alembic/versions/2026_*_github_pr_revision_head_sha_unique.py`

**Deliverable:** `alembic upgrade head` on dev DB; **skip subphase entirely if R0 locked A**.

**LOOP note:** Pause after migration subphase for operator staging apply.

---

## R1.4 — Concurrent synchronize tests

**What:** Integration-style unit tests:

1. Two parallel synchronize calls with **same** `head_sha` → one revision row; second returns without worker failure.
2. Two parallel calls with **different** SHAs → two revision rows; monotonic `revision_number`; no `IntegrityError` surfaced to worker.
3. Sequential different SHAs → two rows.

**Files:** `backend/tests/unit/test_github_pull_requests.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_pull_requests.py -q -k "revision or synchronize"
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_pull_requests.py tests/unit/test_github_webhooks.py -q
pipenv run ruff check app/services/github_pull_requests.py
```

**Next:** [REVY_REVIEW_DOGFOOD_R2_EXECUTION.md](./REVY_REVIEW_DOGFOOD_R2_EXECUTION.md)
