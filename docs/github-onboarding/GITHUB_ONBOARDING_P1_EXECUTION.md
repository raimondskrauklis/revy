# docs/github-onboarding/GITHUB_ONBOARDING_P1_EXECUTION.md

# P1 — Setup/Callback hops + persist + honest checklist (execution)

Phase **P1** of [`GITHUB_ONBOARDING_GENERAL_PLAN.md`](./GITHUB_ONBOARDING_GENERAL_PLAN.md). Baseline: [`GITHUB_ONBOARDING_FINDINGS.md`](./GITHUB_ONBOARDING_FINDINGS.md) Q12–Q15, Q17–Q21. **P1 only.**

**Goal:** GitHub can return to public API hops with no Revy JWT; Revy binds the installation from HMAC + GitHub user token; a P1-only merge cannot complete Connect GitHub via row count.

## Decisions locked for P1

- Q20 — GET Setup and GET Callback have **no** `Depends(get_current_user)` / no `HTTPBearer`. Bind from install HMAC + GitHub user token.
- Q12 — paths `/api/v1/github/setup` and `/api/v1/github/callback` (new router included from `backend/app/api/v1/__init__.py`, not under `/workspaces`).
- Q13 — Setup stashes `installation_id` (+ `setup_action`) in **HttpOnly** cookie, **SameSite=Lax**, path `/api/v1/github`, max-age 1800, **Secure** when Setup URL is `https`. Then 302 to GitHub authorize with **OAuth** `state` and `redirect_uri` = Callback URL.
- Q15 — same workspace + same GitHub id → idempotent bind (update account metadata; do not 409). Other workspace → existing unique conflict copy. Do not call naive `create_github_installation` on update.
- Q17 — after bind, `enqueue_installation_repository_sync`. First `installation` / `installation_repositories` orphans stay expected.
- Q18 — persist loads workspace from HMAC `workspace_id` and uses `workspace_has_feature(..., "installations.create")`. Fail closed with SPA 302 `plan_upgrade_required`, not a GitHub-looking error.
- Q19 / Q21 — handwritten Alembic `verified_at` timestamptz **nullable**. New inserts **null**. One-time backfill `verified_at = created_at` where `status = 'active'`. List schema + FE type include `verified_at`. Checklist `connect_integration` iff ≥1 row with `verified_at` set. Do not set `verified_at` from the repo list here (P3).
- Discard GitHub user access token after `GET /user/installations` check. New App JWT helper `GET /app/installations/{id}` for account metadata.
- Success/error after hops: **302** to `{APP_PUBLIC_URL}/installations` (query `setup_error` on failure). No JSON body to GitHub’s browser.

## Out of scope for P1 (later phases)

- Start-connect JWT API, stepper, Install button, fallback i18n → **P2**
- Live `list_installation_repositories` to **set** `verified_at`; Configure empty-list UX → **P3**
- Live App dashboard paste, saas-base dogfood → **P4**
- `Depends(get_current_user)` on Setup/Callback
- Creating rows from webhooks

---

## P1.1 — Migration `verified_at` + backfill

**What:** Hand-written revision `2026_09_19_1800_0034_github_installation_verified_at` (`down_revision` = `2026_09_16_2100_0033_github_pull_request_merged`). Add nullable `verified_at` timestamptz on `github_installations`. `UPDATE … SET verified_at = created_at WHERE status = 'active' AND verified_at IS NULL`. Downgrade drops the column. ORM + `GitHubInstallationResponse` field.

**Files:** `backend/alembic/versions/2026_09_19_1800_0034_github_installation_verified_at.py` (new), `backend/app/models/github_installation.py`, `backend/app/schemas/github_installation.py`

**Deliverable:** revision is handwritten; new inserts can be null; backfill SQL is in `upgrade()`.

```bash
cd backend && pipenv run ruff check app/models/github_installation.py app/schemas/github_installation.py
```

**LOOP pause:** stop after this subphase for human migration review before P1.2.

---

## P1.2 — GitHub App + user-token helpers

**What:** `GET /app/installations/{id}` with App JWT (account login/type/id). Exchange OAuth `code` at GitHub; `GET /user/installations` with that user token; require the Setup `installation_id` in the list; drop the token. Reuse `list_installation_repositories` later (P3), not here.

**Files:** `backend/app/integrations/github_api.py`, `backend/tests/unit/test_github_api.py`

**Deliverable:** helpers covered without hitting live GitHub; association miss is a typed error, not persist.

```bash
cd backend && pipenv run pytest tests/unit/test_github_api.py -q
```

---

## P1.3 — Public Setup + Callback hops (HMAC only)

**What:** New router GET `/api/v1/github/setup` and GET `/api/v1/github/callback`. **No** `get_current_user`. Setup: verify install HMAC `state`; stash cookie SameSite=Lax (**Secure** if `https`); 302 to GitHub authorize (`client_id`, OAuth `state`, `redirect_uri` = Callback). Callback: verify OAuth `state`; read stash; user-token association; App GET metadata; bind; clear cookie; 302 SPA. Missing `state` / OAuth-without-install / spoofed id → 302 `setup_error`, no persist. Tests: **no** `Authorization` header; TestClient `follow_redirects=False` so the 302 is asserted (do not follow to GitHub).

**Files:** `backend/app/api/v1/github_setup.py` (new), `backend/app/api/v1/__init__.py`, `backend/app/services/github_install_state.py` (OAuth `state` + cookie blob), `backend/tests/unit/test_github_setup_routes.py` (new)

**Deliverable:** TestClient GET setup without Bearer, `follow_redirects=False`, still 302s to GitHub when HMAC is valid; forged `installation_id` does not insert a row.

```bash
cd backend && pipenv run pytest tests/unit/test_github_setup_routes.py -q
```

---

## P1.4 — Idempotent bind + R1 enqueue + plan gate

**What:** `bind_github_installation` (new): same workspace+id updates metadata and returns existing row; other workspace raises existing conflict; new row `verified_at=None`, `status=active`. Then `enqueue_installation_repository_sync`. Plan check via `workspace_has_feature` on HMAC workspace (not path `Depends`). Extend `test_github_installations.py` so Redirect-on-update does **not** 409.

**Files:** `backend/app/services/github_installations.py`, `backend/tests/unit/test_github_installations.py`

**Deliverable:** second bind same workspace+id succeeds; other workspace still conflicts; enqueue called once per successful bind.

```bash
cd backend && pipenv run pytest tests/unit/test_github_installations.py tests/unit/test_github_setup_routes.py -q
```

---

## P1.5 — Checklist + FE type read `verified_at`

**What:** `GitHubInstallation.verified_at: string | null`. `ChecklistContext` grows a verified predicate (e.g. `hasVerifiedInstallation` from `installations.some((row) => row.verified_at)`). Checklist `connect_integration` uses that, **not** `installationCount > 0`. Keep `installationCount` for the summary widget (row count, including unverified). Grandfathered backfilled rows stay complete; a new P1 row with `verified_at: null` does not. Update **every** mock that treats `installationCount: 1` as “Connect GitHub complete”.

**Files:** `frontend/src/features/installations/api.ts`, `frontend/src/features/dashboard/hooks.ts`, `frontend/src/features/dashboard/checklistSteps.ts`, `frontend/src/features/dashboard/checklistSteps.test.ts`, `frontend/src/features/dashboard/widgets/SetupChecklistWidget.test.tsx`, `frontend/src/features/dashboard/pages/DashboardPage.test.tsx`

**Deliverable:** `installationCount: 1` with `verified_at: null` does **not** complete Connect GitHub; a row with `verified_at` set does. Widget “hides when complete” mock uses the verified predicate.

```bash
cd frontend && npm test -- checklistSteps SetupChecklistWidget DashboardPage
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_install_state.py tests/unit/test_github_api.py tests/unit/test_github_setup_routes.py tests/unit/test_github_installations.py -q
pipenv run ruff check app/api/v1/github_setup.py app/services/github_installations.py app/integrations/github_api.py app/models/github_installation.py app/schemas/github_installation.py
```

**Phase gate** (from `frontend/`):

```bash
npm test -- checklistSteps SetupChecklistWidget DashboardPage
```

**Deploy:** ship migration before API/FE read `verified_at`. Do not paste live App URLs yet (P4).

**Next:** [`GITHUB_ONBOARDING_P2_EXECUTION.md`](./GITHUB_ONBOARDING_P2_EXECUTION.md)
