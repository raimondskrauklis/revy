# GitHub surface hardening P2 — GraphQL scale (execution)

Phase **P2** of [GITHUB_SURFACE_HARDENING_GENERAL_PLAN.md](./GITHUB_SURFACE_HARDENING_GENERAL_PLAN.md). Baseline: [GITHUB_SURFACE_HARDENING_FINDINGS.md](./GITHUB_SURFACE_HARDENING_FINDINGS.md) §5, GH-2, GH-3, GH-Q3. **P2 only.**

**Goal:** One paginated thread index per publish; store `thread_id`; ≤2 GraphQL list calls.

## Decisions locked for P2

- Add `list_review_threads` with cursor pagination in `github_api.py`.
- Build `databaseId → threadId` map once per publish; resolve uses index (no per-group list query).
- On new inline comment: store `thread_id` in v2 map when lookup succeeds (may resolve thread id on next publish if not returned by REST).
- `find_review_thread_id_for_comment` delegates to shared index or paginated list.

## Out of scope for P2

- Customer rate-limit policy UI
- Option B `resolution_status` trigger

---

## P2.1 — Paginated list_review_threads

**What:** Implement `list_review_threads(client, …) -> list[thread]` with GraphQL cursor pagination for threads and comments (page until exhausted or safety cap documented in code).

**Files:** `backend/app/integrations/github_api.py`, `backend/tests/unit/test_github_api_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_api_publish.py -k "list_review_threads" -q
```

---

## P2.2 — Index-backed resolve

**What:** Refactor `_resolve_superseded_inline_threads` to accept prebuilt `comment_id → thread_id` index; `run_publish_job` fetches index once before resolve loop.

**Files:** `backend/app/services/github_publish.py`, `backend/app/integrations/github_api.py`

**Deliverable:** Unit test asserts single list call services multiple fingerprint resolves (mock call count).

---

## P2.3 — Persist thread_id on inline post

**What:** After `create_pull_request_review_comment`, optionally resolve thread_id from index; write v2 map entry with both ids.

**Files:** `backend/app/services/github_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish.py -k "thread_id" -q
```

---

## P2.4 — Busy PR pagination test

**What:** Unit test: >100 thread nodes across pages — target comment_id still found (GH-2 correctness).

**Files:** `backend/tests/unit/test_github_api_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_api_publish.py -k "pagination" -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest \
  tests/unit/test_github_publish.py \
  tests/unit/test_github_api_publish.py -q
```

**Human gate:** none.

**Next:** [GITHUB_SURFACE_HARDENING_P3_EXECUTION.md](./GITHUB_SURFACE_HARDENING_P3_EXECUTION.md)
