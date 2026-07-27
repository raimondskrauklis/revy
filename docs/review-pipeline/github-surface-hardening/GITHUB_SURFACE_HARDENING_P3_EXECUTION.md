# GitHub surface hardening P3 — Edge cases (execution)

Phase **P3** of [GITHUB_SURFACE_HARDENING_GENERAL_PLAN.md](./GITHUB_SURFACE_HARDENING_GENERAL_PLAN.md). Baseline: [GITHUB_SURFACE_HARDENING_FINDINGS.md](./GITHUB_SURFACE_HARDENING_FINDINGS.md) GH-4, GH-5. **P3 only.**

**Goal:** Same-SHA re-publish idempotent; visible skip when inline data incomplete.

## Decisions locked for P3

- GH-1b (persist after resolve) ships in P1 — P3 verifies same-SHA does not double-resolve or lose map.
- Missing `group_id`: structured warning log with `publish_job_id`, `finding_id` — not silent `continue` only.
- No reconcile changes.

## Out of scope for P3

- Test harness wide refactor → **P4**
- Human dogfood sign-off → **P4**

---

## P3.1 — Same-SHA re-publish test

**What:** Extend or replace `test_run_publish_job_resolves_superseded_threads_when_inline_already_posted` (~1254–1357): assert `summary_json["github_inline_threads"]` v2 persistence after resolve when `post_inline=False` and same `head_sha` re-publish — no duplicate GraphQL resolve calls (mock assert). Prior test mocks resolve; new/extended test must assert real map persistence path from P1 GH-1b.

**Files:** `backend/tests/unit/test_github_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish.py -k "same_sha or re_publish" -q
```

---

## P3.2 — Missing group_id warning

**What:** When inline finding has `group_id is None`, log `github_publish_inline_skipped_no_group` with ids; keep skip behavior.

**Files:** `backend/app/services/github_publish.py`, `backend/tests/unit/test_github_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish.py -k "no_group" -q
```

---

## P3.3 — Re-activation same publish

**What:** Test resolve-before-inline order: fingerprint removed from map then re-posted in same publish when finding returns in current run.

**Files:** `backend/tests/unit/test_github_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish.py -k "reactivat" -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest tests/unit/test_github_publish.py -q
```

**Human gate:** none.

**Next:** [GITHUB_SURFACE_HARDENING_P4_EXECUTION.md](./GITHUB_SURFACE_HARDENING_P4_EXECUTION.md)
