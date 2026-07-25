# docs/saas-base/waves/SAAS_BASE_W0_EXECUTION.md

# W0 — Shell & workspace APIs (execution)

Wave **W0** of [`SAAS_BASE_W0_SHELL_GENERAL_PLAN.md`](../SAAS_BASE_W0_SHELL_GENERAL_PLAN.md). Baseline: [`SAAS_BASE_FINDINGS.md`](../SAAS_BASE_FINDINGS.md) § Workspace API ownership, [`SETTINGS_IA.md`](../SETTINGS_IA.md). **W0 only.**

**Goal:** Settings shell layout, app header (switcher + user menu), and workspace/team backend APIs — **no settings sidebar links** until W1.

**Authority:** `internal-docs/starter-pack/docs/backend/TENANCY.md`, `INVITATIONS.md`, `frontend/reference/ROUTING.md`.

## Decisions locked for W0

- Hand-written Alembic only — **no migration in W0** (uses existing `users`, `workspaces`, `workspace_memberships`, `workspace_invitations`).
- Workspace rename: `PATCH /api/v1/workspaces/{workspace_id}` — body `{ "name": "..." }` only; workspace `admin` only; **slug immutable** in W0.
- Member APIs under `/api/v1/workspaces/{workspace_id}/members` — cursor list, `PATCH` role, `DELETE` remove.
- Invitation list + revoke under `/api/v1/workspaces/{workspace_id}/invitations` — extend existing create route file; **list omits `token`** (use `InvitationListItem`).
- Last-admin guard on member **remove** and **role demotion** (`PATCH`) — service layer, tested.
- Self remove/demote allowed when another `admin` remains in the workspace.
- No `record_audit` / `api_audit` writes — audit table and team mutation rows ship **W2**.
- Settings sidebar: **zero section links** in W0 (groups may render empty); `/settings` index = neutral shell (`settings.shell.title`), **no redirect** to `/settings/profile` until **W1**.
- Remove `QuietComponentsDemo` from `/settings` route — replace with `SettingsLayout` + empty outlet.
- Extension registry (`platform/extensions`) → **W3**, not W0.
- `RequirePermission` FE guards on workspace settings **sub-routes** when linked — **W2**; W0 ships shell only (API RBAC server-side).
- Unit tests only under `backend/tests/unit/`; Vitest for touched FE components.
- EN+LV for all new user-facing strings.

## Out of scope for W0 (later waves)

- Settings page content (profile, security, appearance) → **W1**
- Team/workspace settings UI tables → **W2**
- `api_audit` migration → **W2**
- Dashboard widgets, checklist → **W3**
- Billing → **W4**
- Platform admin UI → **W5**
- Personal API keys, notifications, file handling → **deferred program**

---

## W0.1 — Workspace + member services & routes

**What:** Service functions + FastAPI routes for workspace general update and membership management.

| Method | Path | Permission |
|--------|------|------------|
| `PATCH` | `/api/v1/workspaces/{workspace_id}` | `admin:users` + `require_same_workspace` — body: `{ "name": string }` |
| `GET` | `/api/v1/workspaces/{workspace_id}/members` | `items:view` (any member) — cursor pagination |
| `PATCH` | `/api/v1/workspaces/{workspace_id}/members/{user_id}` | `admin:users` — body: `{ "role": "admin"\|"operator"\|"viewer" }`; last-admin guard on demotion |
| `DELETE` | `/api/v1/workspaces/{workspace_id}/members/{user_id}` | `admin:users` — last-admin guard |

**Response shapes:** `WorkspaceUpdate` / `WorkspaceResponse` (`id`, `name`, `slug`, `status`); `MemberListItem` (`user_id`, `email`, `full_name`, `role`, `created_at`) in `CursorResponse`.

**Files:** `backend/app/services/workspaces.py` (new), `backend/app/services/memberships.py` (new), `backend/app/api/v1/workspaces/settings.py` (PATCH), `backend/app/api/v1/workspaces/members.py` (new), `backend/app/api/v1/workspaces/__init__.py` (register routers), `backend/app/schemas/workspaces.py`, `backend/app/schemas/memberships.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_workspaces.py tests/unit/test_memberships.py -q` — green (create tests in this subphase).

---

## W0.2 — Invitation list + revoke APIs

**What:** Extend invitations service with list (cursor) + revoke; wire GET + DELETE on workspace invitations router.

| Method | Path | Permission |
|--------|------|------------|
| `GET` | `/api/v1/workspaces/{workspace_id}/invitations` | `admin:users` — default `status=pending`; optional `?status=` filter |
| `DELETE` | `/api/v1/workspaces/{workspace_id}/invitations/{invitation_id}` | `admin:users` — set `status=revoked`; **404** if not `pending` |

**List contract:** `CursorResponse[InvitationListItem]` — **no `token`** field (unlike create `InvitationResponse`).

**Files:** `backend/app/services/invitations.py`, `backend/app/api/v1/workspaces/invitations.py`, `backend/app/schemas/invitations.py`, `backend/tests/unit/test_invitations.py` (extend existing)

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_invitations.py -q` — green including new list/revoke cases.

---

## W0.3 — Settings layout shell + router

**What:** Nested `/settings` layout with Personal / Workspace **group labels** and empty `<Outlet />` — **no NavLink** to profile/security/etc. yet. `/settings` index shows neutral shell title (`settings.shell.title`); **no redirect** to `/settings/profile` (W1). Remove `QuietComponentsDemo` from production path.

**Router tree:**

```text
/settings → AppShellLayout → SettingsLayout → index (SettingsShellPage)
```

Do **not** replace `AppShellLayout` with `SettingsLayout` at the top level.

**Files:** `frontend/src/features/settings/layout/SettingsLayout.tsx`, `frontend/src/features/settings/layout/SettingsSidebar.tsx`, `frontend/src/lib/routerInstance.tsx`, `frontend/src/features/settings/pages/SettingsShellPage.tsx` (minimal; replace `SettingsPage` usage), delete or relocate `QuietComponentsDemo` to test-only if still needed

**Deliverable:** `cd frontend && npm test -- --run SettingsLayout` — green; `npm run build` succeeds; visiting `/settings` shows layout without links to unimplemented sections.

---

## W0.4 — App header: workspace switcher + user menu

**What:** `AppHeader` in `AppShellLayout` (visible on mobile — main sidebar stays `md+`) — workspace dropdown when `memberships.length > 1` (or always show current workspace name); user menu with profile link (href `/settings` in W0; W1 retargets to `/settings/profile`), sign out via `logout()` from `AuthContext`. On switch: `setActiveWorkspace()` from `@/lib/me` + `refetchUser()` (updates `X-Workspace-Id` via existing `api.ts` interceptor).

**Files:** `frontend/src/components/layout/AppHeader.tsx`, `frontend/src/components/layout/AppShellLayout.tsx`, `frontend/src/components/layout/WorkspaceSwitcher.tsx`, `frontend/src/components/layout/UserMenu.tsx`, `frontend/src/i18n/locales/en.json`, `frontend/src/i18n/locales/lv.json`

**Deliverable:** `cd frontend && npm test -- --run WorkspaceSwitcher UserMenu` — green.

---

## W0.5 — FE API clients + types for W0 endpoints

**What:** TanStack-ready API functions + types for members list, workspace PATCH, invitations list/revoke (used by **W2** UI; W0 ships clients + query keys). **Do not** rewire header switcher here — W0.4 uses `@/lib/me`. Hooks should call `queryClient.invalidateQueries()` on workspace switch when workspace-scoped keys exist.

**Files:** `frontend/src/features/settings/api.ts`, `frontend/src/features/settings/types.ts`, `frontend/src/features/settings/hooks.ts` (query keys only OK)

**Deliverable:** `cd frontend && npm test -- --run settings` — green for new api/hook unit tests.

---

## W0.6 — SETTINGS_IA mirror + README

**What:** Copy committed [`SETTINGS_IA.md`](../SETTINGS_IA.md) to `internal-docs/starter-pack/docs/frontend/patterns/SETTINGS_IA.md` (starter-pack sync; `internal-docs/` is gitignored — manual check for contributors with repo access). Update [README.md](./README.md) W0 status when done.

**Files:** `internal-docs/starter-pack/docs/frontend/patterns/SETTINGS_IA.md`, `docs/saas-base/waves/README.md`

**Deliverable:** `test -f internal-docs/starter-pack/docs/frontend/patterns/SETTINGS_IA.md` — exists locally (not CI-gated).

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest tests/unit/test_workspaces.py tests/unit/test_memberships.py tests/unit/test_invitations.py -q
```

**Phase gate** (from `frontend/`):

```bash
npm run lint && npm test -- --run SettingsLayout WorkspaceSwitcher UserMenu settings && npm run build
```

**Deploy:** none — API + shell only.

**Next:** [SAAS_BASE_W1_EXECUTION.md](./SAAS_BASE_W1_EXECUTION.md)
