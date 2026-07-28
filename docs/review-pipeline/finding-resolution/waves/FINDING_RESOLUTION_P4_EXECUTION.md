# Finding resolution P4 — Human dismiss + hardening (execution)

Phase **P4** of [FINDING_RESOLUTION_GENERAL_PLAN.md](../FINDING_RESOLUTION_GENERAL_PLAN.md). **P4 only.**

**Goal:** Workspace admin can dismiss a finding group; FR-Q7 two-block summary parity; RG-6 partial LLM failure tests; reviewer UI labels.

## Decisions locked for P4

- `POST /v1/workspaces/{workspace_id}/repositories/{repository_id}/pull-requests/{pull_request_id}/finding-groups/{group_id}/dismiss` (same router as reconciled findings — `installation_review.py`).
- Auth: `Permission.admin_users` + `require_same_workspace` (FR-Q15) — not platform super-admin.
- Optional dismiss `reason` → **`record_audit()`** metadata only — **no** `judge_notes` on group (field lives on `GitHubFindingJudgeOutcomeORM`); **no** new dismiss-reason column in P4.
- Sets `state=resolved`, `resolution_method=human_dismissed`, `resolved_at_revision_id` = PR HEAD revision.
- FR-Q7 summary: block (1) this-generation publishable inline; block (2) all PR-level `active` still open — inline comment = generation only.
- RG-6: partial discovery judge failure → `skipped_unavailable` (already); add tests for mixed success/failure outcomes.

## Out of scope for P4

- Full R7.6 ack/merge UX
- Post-merge batch (FR-Q10)

---

## P4.1 — Dismiss API endpoint

**What:** Route + service `dismiss_finding_group(...)` with tenancy checks; 404 when group not on PR; `record_audit` when `reason` provided.

**Files:** `backend/app/api/v1/workspaces/installation_review.py`, `backend/app/services/github_finding_closure.py`, `backend/tests/unit/test_github_reconciled_findings_routes.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_reconciled_findings_routes.py -k dismiss -q
```

---

## P4.2 — FR-Q7 two-block publish summary

**What:** `format_summary_comment` emits generation block + PR-level still-open block; tests assert inline publish uses generation-only subset.

**Files:** `backend/app/services/github_publish_formatter.py`, `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py -k "summary or two_block" -q
```

---

## P4.3 — RG-6 partial judge failure tests

**What:** Mock judge: 3 candidates, 1 LLM error → step `skipped_unavailable`; publish not blocked; remaining outcomes persisted. Net-new tests — behavior already in `_judge_candidates_missing_outcome`.

**Files:** `backend/tests/unit/test_github_finding_judge.py`, `backend/tests/unit/test_reconcile_tasks.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_finding_judge.py tests/unit/test_reconcile_tasks.py -k "skipped_unavailable or partial" -q
```

---

## P4.4 — Publish parity test (Babysit-grade)

**What:** Integration-style unit test: reconciled API fields match publish formatter counts for same fixture PR.

**Files:** `backend/tests/unit/test_github_publish_formatter.py`, `backend/tests/unit/test_github_reconciled_findings_routes.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py tests/unit/test_github_reconciled_findings_routes.py -k parity -q
```

---

## P4.5 — Reviewer UI resolution labels + dismiss (EN + LV)

**What:** Extend `ReconciledFinding` type + `FindingRow` with `resolution_status` / `resolution_method` badges via `t()`; admin dismiss action on active groups (calls P4.1 route). Keys in `frontend/src/i18n/locales/en.json` + `lv.json` under `reviewer.resolution.*`.

**Files:** `frontend/src/features/reviewer/types.ts`, `frontend/src/features/reviewer/components/FindingRow.tsx`, `frontend/src/features/reviewer/api.ts`, `frontend/src/i18n/locales/en.json`, `frontend/src/i18n/locales/lv.json`

**Deliverable:**

```bash
cd frontend && npm test -- --run FindingRow
cd frontend && npm run lint
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_reconciled_findings_routes.py tests/unit/test_github_publish_formatter.py tests/unit/test_github_finding_judge.py tests/unit/test_reconcile_tasks.py -q
pipenv run ruff check app/api/v1/workspaces/installation_review.py app/services/github_finding_closure.py
```

**Phase gate** (from `frontend/`):

```bash
npm test -- --run
npm run lint
```

**Next:** [FINDING_RESOLUTION_P5_EXECUTION.md](./FINDING_RESOLUTION_P5_EXECUTION.md)
