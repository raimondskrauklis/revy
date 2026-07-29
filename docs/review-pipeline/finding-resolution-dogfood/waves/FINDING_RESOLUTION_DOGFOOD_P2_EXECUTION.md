# Finding resolution dogfood P2 — FR-DG2 stale retirement (execution)

Phase **P2** of [FINDING_RESOLUTION_DOGFOOD_GENERAL_PLAN.md](../FINDING_RESOLUTION_DOGFOOD_GENERAL_PLAN.md). Baseline: findings § FR-DG2. **P2 only.**

**Goal:** Removing flagged code closes group, shrinks block 2 `pr_active_count`, resolves stale inline per GH-1v2.

## Decisions locked for P2

- **Absent + addressed:** fingerprint not in run N + `resolution_status=addressed` from Pass 1 → `state=resolved`, `resolution_method=absent_and_addressed` (FR-Q3).
- **PR-wide table:** `verdict_groups` / `pr_active_groups` query excludes `resolved` / `superseded` groups.
- **Thread collapse:** fingerprint in `_fingerprints_to_resolve_inline_threads` when group closed or not publishable; handle `line: null` orphaned threads.
- **Depends on P1:** manifest must show addressed transition on same fix push.

## Out of scope for P2

- Manifest prior-revision logic → **P1** (done)
- Moonshot discovery changes → **P4**
- Operator sign-off doc sync → **P3**

---

## P2.1 — Pass 2 absent closure wiring

**What:** Ensure reconcile Pass 2 closes groups when fingerprint absent and Pass 1 stamped `addressed`; unit tests with mock groups.

**Files:** `backend/app/services/github_finding_reconcile.py`, `backend/app/services/github_finding_closure.py`, `backend/tests/unit/test_github_finding_closure.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_closure.py -q
```

---

## P2.2 — PR-wide active set filter

**What:** Publish path loads `pr_active_groups` without resolved/superseded; block 2 row count matches `pr_active_count`.

**Files:** `backend/app/services/github_publish.py`, `backend/app/services/github_publish_formatter.py`, `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py -k "pr_active or verdict" -q
```

---

## P2.3 — Stale inline thread resolve

**What:** Extend `_resolve_stale_inline_threads` / fingerprint map so closed groups and orphaned line threads resolve on GitHub (mock GraphQL in unit tests).

**Files:** `backend/app/services/github_publish.py`, `backend/tests/unit/test_github_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish.py -k "resolve_stale or inline_thread" -q
```

---

## P2.4 — Dogfood push 3 verification

**What:** On same fix push as P1.4 (or follow-up push if needed), confirm `pr_active_count` decreased vs push 1; inline collapsed in GitHub + `summary_json.github_inline_threads`.

**Files:** staging memo only

**Deliverable:** Memo push-2/3 rows PASS for FR-DG2 criteria.

**Human gate:** Operator verifies GitHub inline state.

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_finding_closure.py tests/unit/test_github_publish_formatter.py tests/unit/test_github_publish.py -q
```

**Next:** [FINDING_RESOLUTION_DOGFOOD_P3_EXECUTION.md](./FINDING_RESOLUTION_DOGFOOD_P3_EXECUTION.md)
