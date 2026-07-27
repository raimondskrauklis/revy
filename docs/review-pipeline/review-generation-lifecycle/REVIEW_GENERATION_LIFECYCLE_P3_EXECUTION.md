# Review generation lifecycle P3 — Full surface flush (execution)

Phase **P3** of [REVIEW_GENERATION_LIFECYCLE_GENERAL_PLAN.md](./REVIEW_GENERATION_LIFECYCLE_GENERAL_PLAN.md). Baseline: findings RG-3, RG-Q7. **P3 only.**

**Goal:** No GitHub spill on any channel — one write sequence at publish end for authoritative generation.

## Decisions locked for P3

- Refactor `run_publish_job` into **build** phase (in-memory) + **flush** phase (GitHub APIs).
- **Build:** `compute_check_conclusion`, `build_publish_format_result_async`, load thread map, compute which fingerprints need new inline and which need Option A resolve — **no GitHub API calls** in build.
- **Flush:** ordered sequence — `build_review_thread_comment_index` (GraphQL) → Option A `_resolve_stale_inline_threads` → update/create check run with final conclusion → issue comment → inline REST posts; one `summary_json` persist; `inline_comments_posted = True`.
- Remove `_checkpoint_publish_surface` calls **between** inline posts; at most one persist after full flush (plus failure paths).
- G10 check remains `in_progress` until flush completes (authoritative gen only — P1/P2 already skip non-authoritative).
- Sequential inline REST (RG-Q5) — no GitHub multi-comment review API.

## Out of scope for P3

- Coalesce → **P4**
- Judge candidate filter → **P5**
- Unify summary vs inline group scope (§3c pre-existing)

---

## P3.1 — Extract build/flush structure

**What:** Split `run_publish_job` into private `_build_publish_surface(...)` returning a frozen dataclass / typed dict with: `check_summary`, `issue_comment`, `conclusion`, `inline_threads`, `inline_posts: list[InlinePostSpec]`, `fingerprints_to_resolve`. **No httpx / `github_api` calls in build.**

**Flush order (locked):** `build_review_thread_comment_index` → `_resolve_stale_inline_threads` → check finalize → issue comment → inline posts.

**Files:** `backend/app/services/github_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run ruff check app/services/github_publish.py
```

---

## P3.2 — Remove mid-pass GitHub writes

**What:** Move check run update, issue comment update/create, and all inline `create_pull_request_review_comment` into `_flush_publish_surface`. Delete `_checkpoint_publish_surface` invocations inside the inline loop.

**Files:** `backend/app/services/github_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish.py -k "run_publish_job" -q --tb=no 2>&1 | tail -3
```

---

## P3.3 — Spill regression tests

**What:** Tests with mocked `github_api`:

1. Count `github_api` calls during publish — check + issue + inline happen only in flush (use call order list).
2. No `_checkpoint_publish_surface` / mid-loop persist **between** first and last inline post (single end-of-flush commit OK).
3. Existing publish tests still pass (resolve, reactivation, same-SHA).

**Files:** `backend/tests/unit/test_github_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish.py -k "surface_flush or run_publish_job or no_checkpoint_between_inline" -q
```

---

## P3.4 — Publish harness alignment

**What:** Update autouse fixtures / harness if they assumed mid-loop checkpoint side effects; document flush contract in test module docstring.

**Files:** `backend/tests/unit/test_github_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish.py -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run ruff check .
pipenv run pytest tests/unit/test_github_publish.py -q
```

**Next:** [REVIEW_GENERATION_LIFECYCLE_P4_EXECUTION.md](./REVIEW_GENERATION_LIFECYCLE_P4_EXECUTION.md)
