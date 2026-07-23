# docs/starter-pack/SCAFFOLD_P2_EXECUTION.md

# P2 — Registration & platform flows (execution)

Phase **P2** of [`SCAFFOLD_GENERAL_PLAN.md`](./SCAFFOLD_GENERAL_PLAN.md). Baseline: [`SCAFFOLD_FINDINGS.md`](./SCAFFOLD_FINDINGS.md) § Catalog. **P2 only.**

**Goal:** Frontend status gates and pages match real backend registration flows (Mode A + Mode B).

**Authority:** `internal-docs/starter-pack/docs/backend/USER_REGISTRATION.md`, `ME_ENDPOINT.md`.

## Decisions locked for P2

- Implement **full** status machine + admin endpoints even when Mode A is default (empty admin queue OK).
- **Frontend in scope (Q14):** real profile form + admin pending list/actions — not API-only placeholders.
- `POST /api/v1/users/complete-profile` body: display name (and fields per USER_REGISTRATION.md); Mode A → provision + `active`; Mode B → `pending_approval`.
- Admin routes under `/api/v1/admin/users/` — **`require_super_admin()` only** (platform signup queue per USER_REGISTRATION.md Mode B). Do **not** use `Permission.admin_users` / workspace `AppRole.admin` — that permission is for workspace member invites (**P3**).
- FE `/admin/users` — **`isPlatformAdmin` / `RequirePlatformAdmin`** guard, not `RequirePermission permission="admin:users"`.
- EN+LV i18n for all new user-facing strings; domain exceptions only (no bare `HTTPException`).
- Registration flag pairing gate: document Mode B test path in `REGISTRATION_FLAGS.md`.

## Out of scope for P2 (later phases)

- Invitations DB + accept flow → **P3**
- Idempotency header on routes → **P3**
- Revy product domain → **P4**
- Billing routes → carryover; optional cleanup **P3**

---

## P2.1 — Complete-profile API + onboarding tests

**What:** `POST /api/v1/users/complete-profile`; wire `onboarding.py` provisioning; branch on `registration_require_admin_approval`.

**Files:** `backend/app/api/v1/users.py` (new router), `backend/app/services/onboarding.py`, `backend/app/services/users.py`, `backend/app/api/v1/__init__.py`, `backend/tests/unit/test_onboarding.py`, `backend/tests/unit/test_users_complete_profile.py` (new)

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_onboarding.py tests/unit/test_users_complete_profile.py -q` — pass.

## P2.2 — Admin pending / approve / reject APIs

**What:** `GET /api/v1/admin/users/pending`, `POST …/{user_id}/approve`, `POST …/{user_id}/reject`; **`Depends(require_super_admin())`** on all handlers; approve calls shared `activate_user_with_workspace`.

**Files:** `backend/app/api/v1/admin/users.py`, `backend/app/api/v1/admin/__init__.py`, `backend/app/api/v1/__init__.py` (mount admin router), `backend/app/core/auth.py`, `backend/app/services/users.py`, `backend/tests/unit/test_admin_users.py` (new)

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_admin_users.py -q` — pass; tests assert workspace `AppRole.admin` (non–super_admin) receives **403**.

## P2.3 — Complete-profile page (FE)

**What:** Replace `/complete-profile` `StatusGatePage` with form (`QuietInput`); submit to complete-profile API; handle Mode A redirect to dashboard vs Mode B to `/pending-approval`.

**Files:** `frontend/src/features/auth/pages/CompleteProfilePage.tsx`, `frontend/src/lib/routerInstance.tsx`, `frontend/src/features/auth/api.ts` (or colocated api), `frontend/src/i18n/locales/en.json`, `frontend/src/i18n/locales/lv.json`

**Deliverable:** `cd frontend && npm test -- --run CompleteProfile` (add `CompleteProfilePage.test.tsx` if no match).

## P2.4 — Admin users queue (FE)

**What:** Replace `AdminUsersPage` placeholder with pending list, approve/reject actions, empty state for Mode A. Route guard: platform super_admin only.

**Files:** `frontend/src/components/auth/RequirePlatformAdmin.tsx` (new), `frontend/src/lib/routerInstance.tsx` (replace `RequirePermission admin:users` with platform guard), `frontend/src/features/admin/pages/AdminUsersPage.tsx`, `frontend/src/features/admin/api.ts`, `frontend/src/features/admin/components/*`, i18n `admin.*` keys

**Deliverable:** `cd frontend && npm test -- --run AdminUsers RequirePlatformAdmin` — pass; workspace admin without `platform_role=super_admin` cannot reach page.

## P2.5 — Registration docs + flag gate

**What:** Update `REGISTRATION_FLAGS.md` with Mode B verification steps; note `pending_profile` edge case (findings §6).

**Files:** `docs/starter-pack/REGISTRATION_FLAGS.md`, `docs/starter-pack/DEV_BOOTSTRAP.md` (link)

**Deliverable:** Table for Mode A (P1 default) and Mode B (P2); `rg 'VITE_REGISTRATION_REQUIRE' docs/starter-pack/REGISTRATION_FLAGS.md` — match.

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest tests/unit/test_onboarding.py tests/unit/test_users_complete_profile.py tests/unit/test_admin_users.py -q
```

**Phase gate** (from `frontend/`):

```bash
npm run lint && npm test -- --run && npm run build
```

**Deploy:** None.

**Next:** [`SCAFFOLD_P3_EXECUTION.md`](./SCAFFOLD_P3_EXECUTION.md)
