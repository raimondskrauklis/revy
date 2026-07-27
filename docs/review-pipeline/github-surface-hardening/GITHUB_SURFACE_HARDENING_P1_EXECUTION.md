# GitHub surface hardening P1 — Auto-resolve (execution)

Phase **P1** of [GITHUB_SURFACE_HARDENING_GENERAL_PLAN.md](./GITHUB_SURFACE_HARDENING_GENERAL_PLAN.md). Baseline: [GITHUB_SURFACE_HARDENING_FINDINGS.md](./GITHUB_SURFACE_HARDENING_FINDINGS.md) §4, GH-Q6, GH-1b. **P1 only.**

**Goal:** #52-class stale threads collapse on publish — Option A + persistence (GH-1, GH-1b).

## Decisions locked for P1

- **Option A:** resolve fingerprint when ∈ `inline_threads` but ∉ current `review_run_id` publishable finding fingerprints (`inline_publish_findings_statement`).
- Keep existing resolve for groups in `superseded` / `resolved` state.
- **Rename** `_resolve_superseded_inline_threads` → `_resolve_stale_inline_threads` (behavior expands; no sibling function).
- **Dedupe:** collect fingerprints to resolve in one set — Option A (map − publishable) ∪ superseded/resolved groups; one GraphQL resolve per fingerprint per publish.
- After resolve loop: **always** assign `job.summary_json` via `serialize_inline_thread_map` — even when `post_inline=False`.
- Pop map entry **only after** successful `resolveReviewThread`.
- Do **not** use `resolution_status.addressed` (GH-Q2).
- Do **not** change reconcile.

## Out of scope for P1

- Paginated GraphQL → **P2**
- Reconcile absent-group closure → out of program
- Check/summary hiding stale actives → GH-Q7 deferred

---

## P1.1 — Current-run fingerprint set

**What:** Add helper `_publishable_fingerprints_for_run(session, review_run_id) -> set[str]` — fingerprints of groups linked to publishable inline findings for this run. Use in resolve pass.

**Files:** `backend/app/services/github_publish.py`

**Deliverable:** Helper covered by unit test (pure query mock).

---

## P1.2 — Option A resolve pass

**What:** Rename and extend `_resolve_superseded_inline_threads` → `_resolve_stale_inline_threads`: add `review_run_id: UUID` param; resolve when fingerprint in map but not in `_publishable_fingerprints_for_run`; retain superseded/resolved group loop; dedupe fingerprints before GraphQL calls.

Update `run_publish_job` call site (~734–744) to pass `review_run_id=job.review_run_id`.

**Files:** `backend/app/services/github_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish.py -k "resolve_stale or auto_resolve" -q
```

---

## P1.3 — GH-1b persist summary_json

**What:** After resolve completes, reassign `job.summary_json["github_inline_threads"]` using `serialize_inline_thread_map(inline_threads, prior_v2=…)` before flush — unconditional of `post_inline`. Add test: `post_inline=False`, resolve pops entry, persisted `summary_json` is v2 shape and reflects pop.

**Files:** `backend/app/services/github_publish.py`, `backend/tests/unit/test_github_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish.py::test_run_publish_job_persists_thread_map_after_resolve_when_inline_skipped -q
```

(Test name may vary — must assert v2 persistence without inline post.)

---

## P1.4 — Unmocked resolve tests + PRODUCT_PATTERNS

**What:** At least one test calls `_resolve_stale_inline_threads` **without** autouse mock (patch only `github_api` GraphQL). Update PRODUCT_PATTERNS “Resolve review threads when fixed” row (line ~64) to **shipped** with Option A wording.

**Files:** `backend/tests/unit/test_github_publish.py`, `docs/review-pipeline/REVIEW_PIPELINE_PRODUCT_PATTERNS.md`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish.py -k "resolve" -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest \
  tests/unit/test_github_publish.py \
  tests/unit/test_github_api_publish.py -q
```

**Human gate:** Optional early dogfood row in [GITHUB_SURFACE_HARDENING_DOGFOOD.md](./GITHUB_SURFACE_HARDENING_DOGFOOD.md) after staging deploy — thread collapse on fix push. **Required before P4 sign-off.**

**Next:** [GITHUB_SURFACE_HARDENING_P2_EXECUTION.md](./GITHUB_SURFACE_HARDENING_P2_EXECUTION.md)
