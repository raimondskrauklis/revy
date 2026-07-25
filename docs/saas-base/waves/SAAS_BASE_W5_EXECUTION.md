# docs/saas-base/waves/SAAS_BASE_W5_EXECUTION.md

# W5 — Platform admin (execution)

Wave **W5** of [`SAAS_BASE_W5_PLATFORM_GENERAL_PLAN.md`](../SAAS_BASE_W5_PLATFORM_GENERAL_PLAN.md). Baseline: [`SAAS_BASE_FINDINGS.md`](../SAAS_BASE_FINDINGS.md) Q10, Q12, § Platform bootstrap, § D Platform super-admin. **Depends on W2 (`api_audit`), W4 (`workspaces.plan` on detail).** **W5 only.**

**Goal:** Super-admin platform console — workspace directory, KPIs, audit search, settings. **Checkpoint after W5.2** (workspace directory UI) before KPI/audit subphases.

**Authority:** `internal-docs/starter-pack/docs/backend/BOOTSTRAP_SUPER_ADMIN.md`, `docs/starter-pack/REGISTRATION_FLAGS.md`.

## Decisions locked for W5

- All `/api/v1/admin/*` routes: `Depends(require_super_admin())` — `users.platform_role == super_admin` via `CurrentUser.is_super_admin`; **not** `Permission.admin_workspaces` and **not** workspace membership.
- **No in-app user directory** — identity ops via Keycloak Admin link on `/admin/settings`; polish existing Mode B queue at `/admin/users` only.
- **Suspended workspaces:** `POST .../suspend` sets `workspaces.status = suspended`; `unsuspend` → `active`. Tenant APIs for members of a suspended workspace return `ForbiddenError` (`error_code=workspace_suspended`) — enforce in `get_current_user` / workspace resolution when `X-Workspace-Id` points at suspended workspace.
- **Admin workspace APIs:**

  | Method | Path | Purpose |
  |--------|------|---------|
  | `GET` | `/api/v1/admin/workspaces` | Cursor list; `?status=`, `?search=` (name/slug ILIKE) |
  | `GET` | `/api/v1/admin/workspaces/{id}` | Detail (read-first) |
  | `POST` | `/api/v1/admin/workspaces/{id}/suspend` | Set suspended |
  | `POST` | `/api/v1/admin/workspaces/{id}/unsuspend` | Set active |

- **List/detail shapes:** `AdminWorkspaceListItem` (`id`, `name`, `slug`, `status`, `plan`, `member_count`, `created_at`); `AdminWorkspaceDetail` adds `stripe_customer_id` (masked `cus_***`), `updated_at`, optional `recent_audit` stub omitted v1.
- **Platform audit writes:** `platform.workspace.suspended`, `platform.workspace.unsuspended`, `platform.workspace.viewed` (on GET detail only — not list).
- **KPIs:** `GET /api/v1/admin/kpis` → `{ workspaces_total, workspaces_active, workspaces_suspended, users_active, users_pending_approval }`.
- **Audit search:** `GET /api/v1/admin/audit` — cross-tenant; cursor paginated; filters: `workspace_id`, `actor_user_id`, `action_prefix`, `created_at_from`, `created_at_to` (ISO dates); order `(created_at DESC, id DESC)`; uses `AuditListItem` (+ `workspace_id` always set when present).
- **Platform settings:** `GET /api/v1/admin/settings` → read-only `{ registration_require_admin_approval, registration_require_profile_form }` from `settings` (no secrets).
- **Signup queue:** **existing** `GET /admin/users/pending` + approve/reject — do not duplicate; surface count on dashboard + nav link.
- **FE layout:** `AdminLayout` (separate from tenant `AppShellLayout`) — sidebar: Dashboard, Workspaces, Users, Audit, Settings; `RequirePlatformAdmin` wrapper; super_admin-only **Admin** entry in `UserMenu` (not tenant sidebar).
- **Router:** `/admin` → redirect `/admin/dashboard`; migrate existing `/admin/users` under `AdminLayout`.
- Impersonation UI → **W7**; Stripe refunds → external Dashboard link on settings page only.
- EN+LV; service-layer unit tests only.

## Out of scope for W5

- Impersonation → **W7**
- In-app user CRUD / email edit → **deferred program**
- Billing refunds / subscription admin → Stripe Dashboard link

---

## W5.1 — Admin workspace APIs + suspended-tenant guard

**What:** `admin_workspaces.py` service + routes (table above). `record_audit` on suspend/unsuspend/view-detail. Add suspended-workspace guard when resolving active workspace for tenant routes.

**Files:** `backend/app/api/v1/admin/workspaces.py`, `backend/app/services/admin_workspaces.py`, `backend/app/schemas/admin.py`, `backend/app/api/v1/admin/__init__.py`, `backend/app/core/auth.py` (or `tenancy.py` — suspended check), `backend/tests/unit/test_admin_workspaces.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_admin_workspaces.py -q` — green.

---

## W5.2 — Admin layout + workspace directory UI

**What:** `AdminLayout` + sidebar nav. `/admin/workspaces` cursor table (search + status filter); `/admin/workspaces/:id` detail page; suspend/unsuspend with confirm dialog. Register under `RequirePlatformAdmin`.

**Router tree (initial):**

```text
/admin → RequirePlatformAdmin → AdminLayout
  index      → Navigate /admin/dashboard
  workspaces → WorkspacesPage
  workspaces/:workspaceId → WorkspaceDetailPage
```

**Files:** `frontend/src/features/admin/layout/AdminLayout.tsx`, `frontend/src/features/admin/pages/WorkspacesPage.tsx`, `WorkspaceDetailPage.tsx`, `frontend/src/features/admin/api.ts` (workspace admin clients), `frontend/src/lib/routerInstance.tsx`, tests, i18n `admin.workspaces.*` EN+LV

**Deliverable:** `cd frontend && npm test -- --run AdminLayout WorkspacesPage WorkspaceDetailPage` — green.

**Checkpoint:** workspace directory functional — safe to continue W5.3+.

---

## W5.3 — Admin KPI API + dashboard page

**What:** `GET /api/v1/admin/kpis`; `AdminDashboardPage` — stat cards + link to `/admin/users` when `users_pending_approval > 0`.

**Files:** `backend/app/api/v1/admin/kpis.py`, `backend/app/services/admin_kpis.py`, `backend/app/api/v1/admin/__init__.py`, `frontend/src/features/admin/pages/AdminDashboardPage.tsx`, `backend/tests/unit/test_admin_kpis.py`, `AdminDashboardPage.test.tsx`, i18n `admin.dashboard.*`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_admin_kpis.py -q` && `cd frontend && npm test -- --run AdminDashboardPage` — green.

---

## W5.4 — Admin audit search API + UI

**What:** `list_platform_audit()` in `audit_service.py`; `GET /api/v1/admin/audit` with filters; `/admin/audit` page — `QuietInput` filters + cursor table; action labels via `admin.audit.actions.*` i18n.

**Files:** `backend/app/api/v1/admin/audit.py`, `backend/app/services/audit_service.py` (extend), `backend/app/schemas/audit.py`, `frontend/src/features/admin/pages/AuditSearchPage.tsx`, `frontend/src/features/admin/api.ts`, `backend/tests/unit/test_admin_audit.py`, `AuditSearchPage.test.tsx`, i18n EN+LV

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_admin_audit.py -q` && `cd frontend && npm test -- --run AuditSearchPage` — green.

---

## W5.5 — Admin settings + users queue integration

**What:**

| Surface | Behavior |
|---------|----------|
| **`GET /admin/settings`** | Registration flags (read-only) |
| **`/admin/settings`** | KC Admin external link (`getKeycloakAccountUrl` pattern → admin console URL); registration flags display; Stripe Dashboard link (optional env) |
| **`/admin/users`** | Move under `AdminLayout`; reuse `AdminUsersPage` + existing pending API |

**Files:** `backend/app/api/v1/admin/settings.py`, `frontend/src/features/admin/pages/AdminSettingsPage.tsx`, update `AdminUsersPage` nav context, `frontend/src/features/admin/routes.tsx`, i18n `admin.settings.*`

**Deliverable:** `cd frontend && npm test -- --run AdminSettingsPage AdminUsersPage` — green.

---

## W5.6 — Admin router consolidation + chrome

**What:** Final `admin/routes.tsx` — full tree:

```text
/admin → RequirePlatformAdmin → AdminLayout
  index        → Navigate /admin/dashboard
  dashboard    → AdminDashboardPage
  workspaces   → WorkspacesPage
  workspaces/:workspaceId → WorkspaceDetailPage
  users        → AdminUsersPage
  audit        → AuditSearchPage
  settings     → AdminSettingsPage
```

Add **Admin** link to `UserMenu` when `isPlatformAdmin(platform_role)`. Remove duplicate `AppShellLayout` wrapper from `/admin/*` routes.

**Files:** `frontend/src/features/admin/routes.tsx`, `frontend/src/lib/routerInstance.tsx`, `frontend/src/components/layout/UserMenu.tsx`, `docs/saas-base/README.md` (one-line `/admin` bootstrap pointer if missing)

**Deliverable:** `cd frontend && npm run lint && npm run build` — green; manual: non-super_admin cannot reach `/admin/*`.

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest tests/unit/test_admin_workspaces.py tests/unit/test_admin_kpis.py tests/unit/test_admin_audit.py tests/unit/test_admin_users.py -q
```

**Phase gate** (from `frontend/`):

```bash
npm run lint && npm test -- --run AdminLayout WorkspacesPage WorkspaceDetailPage AdminDashboardPage AuditSearchPage AdminSettingsPage AdminUsersPage && npm run build
```

**Human gate:** super_admin bootstrap verified on staging (`BOOTSTRAP_SUPER_ADMIN_EMAIL` + `seed_bootstrap_super_admin.py`) before prod admin exposure.

**Deploy:** seed super_admin; remove `BOOTSTRAP_SUPER_ADMIN_EMAIL` after first login.

**Next:** [SAAS_BASE_W6_EXECUTION.md](./SAAS_BASE_W6_EXECUTION.md)
