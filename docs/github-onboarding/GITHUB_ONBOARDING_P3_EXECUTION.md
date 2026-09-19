# docs/github-onboarding/GITHUB_ONBOARDING_P3_EXECUTION.md

# P3 — Verify granted repo (execution)

Phase **P3** of [`GITHUB_ONBOARDING_GENERAL_PLAN.md`](./GITHUB_ONBOARDING_GENERAL_PLAN.md). Baseline: [`GITHUB_ONBOARDING_FINDINGS.md`](./GITHUB_ONBOARDING_FINDINGS.md) Q5, Q6, Q16, Q19, Q21. **P3 only.**

**Goal:** `verified_at` is set only when live GitHub shows ≥1 granted repo; empty allow-list is Configure-on-GitHub, not checklist success.

## Decisions locked for P3

- Q16 — product predicate is **≥1** repo from live `list_installation_repositories` (already in `github_api.py`). **Not** local `github_repositories` (orphaned until R1). **Not** hardcoded `saas-base`.
- Q5 / Q19 / Q21 — checklist already reads `verified_at` (P1). This phase **sets** it. Do not switch the checklist back to row count.
- Empty GitHub list → leave `verified_at` null; SPA shows Configure `https://github.com/settings/installations/{id}` (GitHub redirects user vs org).
- Q6 fallback `registerInstallation` must run the same verify (or an authenticated `POST …/installations/{id}/verify`) so typed junk cannot complete the checklist.
- Q15 Redirect-on-update re-enters Callback then this verify (idempotent bind already in P1).
- Do not treat empty list as “still syncing” success; Configure is the honest state (findings edge 10).

## Out of scope for P3 (later phases)

- saas-base visibility as a **product** check → **P4** experiment only
- Greptile Enable / Enable All UI (Q11)
- Live App dashboard paste → **P4**
- Rewiring checklist from row count (done in P1)

---

## P3.1 — `verify_granted_repositories`

**What:** Service: call `list_installation_repositories`; if len ≥ 1 set `verified_at = now(UTC)` and return ok; if empty leave null. Used from Callback after bind and from fallback verify.

**Files:** `backend/app/services/github_installations.py`, `backend/app/integrations/github_api.py` (reuse list), `backend/tests/unit/test_github_installations.py`

**Deliverable:** mocked empty list does not set `verified_at`; mocked one repo sets it.

```bash
cd backend && pipenv run pytest tests/unit/test_github_installations.py -q
```

---

## P3.2 — Callback + Redirect-on-update call verify

**What:** After successful P1 bind on Callback (`setup_action` install **or** update), run `verify_granted_repositories`. Do not 409. 302 SPA still happens.

**Files:** `backend/app/api/v1/github_setup.py`, `backend/tests/unit/test_github_setup_routes.py`

**Deliverable:** update hop with same id verifies; empty list keeps `verified_at` null.

```bash
cd backend && pipenv run pytest tests/unit/test_github_setup_routes.py -q
```

---

## P3.3 — Authenticated verify for Q6 fallback

**What:** `POST /api/v1/workspaces/{workspace_id}/installations/{installation_id}/verify` — admin + plan gate. After manual register, page calls verify. Typed id that is not a real/accessible install fails closed without setting `verified_at`.

**Files:** `backend/app/api/v1/workspaces/installations.py`, `frontend/src/features/installations/api.ts`, `frontend/src/features/installations/pages/InstallationsPage.tsx`, `backend/tests/unit/test_github_installations.py`, `backend/tests/unit/test_github_connect_routes.py` (extend: `POST …/verify` admin-gated, mirror `test_github_repository_routes.py` for sync)

**Deliverable:** fallback path cannot mark checklist complete without live ≥1 repo.

```bash
cd backend && pipenv run pytest tests/unit/test_github_installations.py tests/unit/test_github_connect_routes.py -q
cd frontend && npm test -- InstallationsPage checklistSteps
```

---

## P3.4 — Configure-on-GitHub empty allow-list UI

**What:** When a row has `verified_at` null, show EN+LV copy + link `https://github.com/settings/installations/{github_installation_id}`. Not success. Not saas-base-specific.

**Files:** `frontend/src/features/installations/components/InstallationsTable.tsx`, `frontend/src/features/installations/components/InstallationsTable.test.tsx` (new), `frontend/src/i18n/locales/en.json`, `frontend/src/i18n/locales/lv.json`

**Deliverable:** `verified_at: null` renders a link to `https://github.com/settings/installations/{github_installation_id}`. Not success. Not saas-base-specific.

```bash
cd frontend && npm test -- InstallationsTable
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_installations.py tests/unit/test_github_setup_routes.py tests/unit/test_github_api.py tests/unit/test_github_connect_routes.py -q
pipenv run ruff check app/services/github_installations.py app/api/v1/github_setup.py app/api/v1/workspaces/installations.py
```

**Phase gate** (from `frontend/`):

```bash
npm test -- installations checklistSteps InstallationsTable
```

**Next:** [`GITHUB_ONBOARDING_P4_EXECUTION.md`](./GITHUB_ONBOARDING_P4_EXECUTION.md)
