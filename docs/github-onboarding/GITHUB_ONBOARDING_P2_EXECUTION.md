# docs/github-onboarding/GITHUB_ONBOARDING_P2_EXECUTION.md

# P2 — Connect wizard UI (execution)

Phase **P2** of [`GITHUB_ONBOARDING_GENERAL_PLAN.md`](./GITHUB_ONBOARDING_GENERAL_PLAN.md). Baseline: [`GITHUB_ONBOARDING_FINDINGS.md`](./GITHUB_ONBOARDING_FINDINGS.md) Q4, Q6, Q9, Q18, Q20. **P2 only.**

**Goal:** A workspace admin starts connect in Revy (JWT) and is sent to GitHub’s Install URL with HMAC `state`; members do not start connect.

## Decisions locked for P2

- Q20 / Q18 — **start-connect** is the JWT surface: `POST /api/v1/workspaces/{workspace_id}/installations/connect`. `admin:users` + `require_plan_feature("installations.create")`. Mints install HMAC `state` (P0 helper) and returns `{ install_url }` (`https://github.com/apps/{slug}/installations/new?state=…`). Does **not** persist. Empty slug/client/secret → `ServiceUnavailableError`.
- Q4 — only workspace admin sees Install Revy and the manual fallback form. Members see installation status (including unverified).
- Q6 — manual ID form stays, copy = admin/dev fallback (not “until webhook phase”). Fallback create still leaves `verified_at` null (P3 verifies).
- Q9 — no GitHub login. Mode B still blocked by existing `ProtectedRoute`; do not add a second status gate.
- Wizard never puts Setup on a SPA `ProtectedRoute` path.
- EN+LV via `t()`; `--app-*`. Cards: org owner may be required; SSO; **Only select repositories**; authorize ≠ install; `plan_upgrade_required` via `mapApiError` + `showDomainErrorToast`.
- Success return from P1 302 lands on `/installations`. Surface `setup_error` query with i18n.

## Out of scope for P2 (later phases)

- Set `verified_at` from live repo list; Configure empty allow-list → **P3**
- Live App Setup URL paste, saas-base dogfood → **P4**
- JWT on Setup/Callback (forbidden, Q20)
- Keycloak / GitHub as Revy IdP
- saas-base codebase

---

## P2.1 — Start-connect API

**What:** `POST …/installations/connect` next to existing list/create. Permission + plan gate same as create. Body empty. Response `install_url` only. Unit tests: 403 non-admin, `plan_upgrade_required` on free, 503 when slug/secret missing, 200 URL contains slug + `state=`.

**Files:** `backend/app/api/v1/workspaces/installations.py`, `backend/app/schemas/github_installation.py`, `backend/tests/unit/test_github_connect_routes.py` (new)

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_installations.py tests/unit/test_github_connect_routes.py -q
```

---

## P2.2 — Connect GitHub stepper + Install Revy

**What:** On `/installations`, after `me.status === active` and `canRegister`, primary CTA calls start-connect then `window.location.assign(install_url)`. Not a typed installation id. Handle `setup_error` from P1 302.

**Files:** `frontend/src/features/installations/api.ts`, `frontend/src/features/installations/pages/InstallationsPage.tsx`, `frontend/src/features/installations/components/ConnectGitHubPanel.tsx` (new), `frontend/src/features/installations/pages/InstallationsPage.test.tsx` (extend; mock `connectInstallation` next to `fetchInstallations` / `registerInstallation`)

**Deliverable:** admin happy path never submits `RegisterInstallationPayload` unless they open the fallback.

```bash
cd frontend && npm test -- InstallationsPage ConnectGitHubPanel
```

---

## P2.3 — Instruction cards + fallback copy + member view

**What:** Cards (org owner, SSO, Only select repositories, authorize ≠ install). Replace EN+LV `installations.register.description` webhook-stale string. Fallback form visually secondary. Members: table only, no CTA/form.

**Files:** `frontend/src/i18n/locales/en.json`, `frontend/src/i18n/locales/lv.json`, `frontend/src/features/installations/components/RegisterInstallationForm.tsx`, `frontend/src/features/installations/pages/InstallationsPage.tsx`, `frontend/src/features/installations/components/RegisterInstallationForm.test.tsx` (new)

**Deliverable:** EN and LV keys exist for every new string; no raw GitHub chrome as product copy.

```bash
cd frontend && npm test -- InstallationsPage RegisterInstallationForm
```

---

## P2.4 — Plan-gate copy + tests

**What:** Wire start-connect `plan_upgrade_required` (403) through existing `mapApiError` + `showDomainErrorToast`. EN+LV `errors.plan_upgrade_required` **already exist** (`en.json` / `lv.json`) — do not add a second key. Admin vs member CTA visibility in `InstallationsPage.test.tsx`.

**Files:** `frontend/src/i18n/locales/en.json`, `frontend/src/i18n/locales/lv.json`, `frontend/src/features/installations/pages/InstallationsPage.test.tsx`

**Deliverable:**

```bash
cd frontend && npm test -- installations checklistSteps
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_installations.py tests/unit/test_github_connect_routes.py tests/unit/test_github_setup_routes.py -q
pipenv run ruff check app/api/v1/workspaces/installations.py app/schemas/github_installation.py
```

**Phase gate** (from `frontend/`):

```bash
npm test -- installations checklistSteps InstallationsPage
```

**Deploy:** hops exist (P1) but GitHub cannot return until P4 pastes Setup/Callback on the live App.

**Next:** [`GITHUB_ONBOARDING_P3_EXECUTION.md`](./GITHUB_ONBOARDING_P3_EXECUTION.md)
