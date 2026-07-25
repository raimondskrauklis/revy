# docs/saas-base/waves/SAAS_BASE_W2_EXECUTION.md

# W2 — Workspace & team (execution)

Wave **W2** of [`SAAS_BASE_W2_WORKSPACE_TEAM_GENERAL_PLAN.md`](../SAAS_BASE_W2_WORKSPACE_TEAM_GENERAL_PLAN.md). Baseline: [`SAAS_BASE_FINDINGS.md`](../SAAS_BASE_FINDINGS.md) § Audit table, § Workspace API ownership. **Depends on W0 (APIs + settings shell), W1 (personal settings routes).** **W2 only.**

**Goal:** Workspace settings UI, full team management, integrations tab, audit infrastructure.

**Authority:** `internal-docs/starter-pack/docs/backend/AUDIT.md`, `TENANCY.md`, `PERMISSIONS.md`, [SETTINGS_IA.md](../SETTINGS_IA.md).

## Decisions locked for W2

- **No new workspace/member/invitation APIs** — UI + audit only; consumes W0 endpoints + existing `POST .../invitations` create.
- **Migration W2.1** — hand-written Alembic `api_audit` per findings locked schema:
  - `id` UUID PK (`uuid_generate_v7()`), `created_at` TIMESTAMPTZ NOT NULL default `now()`
  - `actor_user_id` UUID NOT NULL FK → `users.id`
  - `impersonator_user_id` UUID NULL FK → `users.id` (unused until W7)
  - `workspace_id` UUID NULL FK → `workspaces.id`
  - `action` TEXT NOT NULL, `resource_type` TEXT NULL, `resource_id` TEXT NULL
  - `metadata` JSONB NOT NULL default `'{}'`
  - Indexes: `(workspace_id, created_at DESC)`, `(created_at DESC)`
- `record_audit(session, *, actor_user_id, workspace_id, action, resource_type, resource_id, metadata, impersonator_user_id=None)` — **same transaction** as mutation (before `commit`); `session.add(AuditLogORM(...))`.
- **Audit actions** (snake_case): `workspace.updated`, `workspace_member.role_changed`, `workspace_member.removed`, `workspace_invitation.created`, `workspace_invitation.revoked`.
- **Audit metadata:** `workspace.updated` → `{ "old_name", "new_name" }`; `workspace_member.role_changed` → `{ "user_id", "old_role", "new_role" }`; `workspace_member.removed` → `{ "user_id", "role" }`; `workspace_invitation.created` → `{ "invitation_id", "email", "role" }`; `workspace_invitation.revoked` → `{ "invitation_id", "email" }`.
- **Last-admin API error:** `ForbiddenError` with `error_code="last_workspace_admin"` — FE maps via `mapApiError` + dedicated i18n key `errors.last_workspace_admin`.
- Workspace **rename UI** loads initial name/slug from active `MeMembership` in `useAuth()` (`workspace_name`, `workspace_slug`) — **no new `GET /workspaces/{id}`** in W2; after PATCH use `WorkspaceResponse` + `refetchUser()` to refresh.
- Workspace suspend → **W5 only**; W2 workspace page is rename only; slug **read-only** with helper copy (`settings.workspace.slugImmutable`).
- `/settings/integrations` — base layout + **Revy card** (installation count + link to `/installations`); canonical connect flow stays on `/installations`.
- **Extension registry (minimal W2):** scaffold `platform/extensions/` with `settings_integration` slot only; `dashboard_widget` finalized in **W3**; register Revy GitHub card at bootstrap.
- Permissions matrix — read-only table on `/settings/team` from `ROLE_PERMISSIONS` mirror (`lib/permissions.ts` + i18n `settings.permissions.*`).
- **Route guards:**
  - `/settings/workspace` — `RequirePermission` `admin:users` (entire route)
  - `/settings/team` — any member (`items:view`); invite/role/remove controls visible only when `admin:users`
  - `/settings/integrations` — any member (`items:view`)
- Sidebar: enable **Workspace** group links (general, team, integrations); billing/danger stay hidden until W4/W6.
- TanStack Query: use W0 `settings/hooks.ts` keys; `invalidateQueries` after team/workspace mutations.
- EN+LV; unit tests only.

## Out of scope for W2

- Billing UI → **W4**
- Danger zone → **W6**
- Platform workspace directory / suspend → **W5**
- Dashboard widgets / audit read API → **W3**
- Invitation resend → **reject** (revoke + create new if needed)

---

## W2.1 — `api_audit` migration + ORM

**What:** Hand-written Alembic revision creating `api_audit` per locked schema. `AuditLogORM` in `app/models/audit_log.py`; export from `models/__init__.py`. `app/schemas/audit.py` — `AuditLogRecord` typed dict / internal shape for `record_audit` (not a public list API yet — W3 adds read).

**Files:** `backend/alembic/versions/YYYY_MM_DD_HHMM_NNNN_api_audit.py`, `backend/app/models/audit_log.py`, `backend/app/models/__init__.py`, `backend/app/schemas/audit.py`, `backend/tests/unit/test_audit_model.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_audit_model.py -q` — green (table metadata, column types, indexes).

**LOOP pause:** `alembic upgrade head` on dev DB before W2.2+.

---

## W2.2 — `record_audit` service + mutation hooks

**What:** `record_audit()` in `audit_service.py`. Wire into:

| Service function | Audit action |
|------------------|--------------|
| `workspaces.update_workspace` (or equivalent) | `workspace.updated` |
| `memberships.update_member_role` | `workspace_member.role_changed` |
| `memberships.remove_member` | `workspace_member.removed` |
| `invitations.create_invitation` | `workspace_invitation.created` |
| `invitations.revoke_invitation` (new or existing revoke helper) | `workspace_invitation.revoked` |

Pass `actor_user_id` from route `current_user.user_id`; `workspace_id` from path; populate `metadata` per locked shapes above.

**Files:** `backend/app/services/audit_service.py`, `backend/app/services/workspaces.py`, `backend/app/services/memberships.py`, `backend/app/services/invitations.py`, `backend/tests/unit/test_audit_service.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_audit_service.py tests/unit/test_workspaces.py tests/unit/test_memberships.py tests/unit/test_invitations.py -q` — green; tests assert `record_audit` / `session.add` called with expected action + metadata.

---

## W2.3 — Workspace general settings UI

**What:** `/settings/workspace` — `QuietInput` workspace name (admin); slug read-only; save → W0 `patchWorkspace()`; `notify.success()` on save; `handleFormError()` on errors; `refetchUser()` after save. Route wrapped in `RequirePermission permission="admin:users"`.

**Files:** `frontend/src/features/settings/pages/WorkspaceSettingsPage.tsx`, `frontend/src/features/settings/hooks.ts` (workspace mutation hook), `frontend/src/lib/routerInstance.tsx`, `frontend/src/i18n/locales/en.json`, `lv.json`

**Deliverable:** `cd frontend && npm test -- --run WorkspaceSettingsPage` — green.

---

## W2.4 — Team settings UI

**What:** `/settings/team` —

| Section | Who sees | Behavior |
|---------|----------|----------|
| **Members table** | all members | Cursor list via `useMembers()`; columns: name, email, role, joined; **admin:** `QuietSelect` role + remove button |
| **Invitations table** | admin only | Pending list + revoke; hidden for non-admin |
| **Invite form** | admin only | `QuietInput` email + `QuietSelect` role → `POST .../invitations` |
| **Permissions matrix** | all members | Read-only; rows = roles, cols = permissions from `lib/permissions.ts` |

Surface `last_workspace_admin` and other domain errors via `mapApiError` / `showDomainErrorToast`. Confirm dialogs for remove/revoke. Cursor **load more** when `has_next`.

**Files:** `frontend/src/features/settings/pages/TeamSettingsPage.tsx`, `frontend/src/features/settings/components/MembersTable.tsx`, `InvitationsTable.tsx`, `InviteMemberForm.tsx`, `PermissionsMatrix.tsx`, `frontend/src/features/settings/hooks.ts`, `frontend/src/features/settings/api.ts` (ensure create-invite client exists), i18n EN+LV

**Deliverable:** `cd frontend && npm test -- --run TeamSettingsPage MembersTable InvitationsTable InviteMemberForm PermissionsMatrix` — green.

---

## W2.5 — Integrations tab + extension slot (minimal)

**What:** Scaffold `frontend/src/platform/extensions/`:

- `slots.ts` — `settings_integration` (+ `dashboard_widget` enum value reserved, unused until W3)
- `registry.ts` — `registerExtension()`, `getExtensions(slot)` (sync); filter by optional `permission` using `hasPermission()`
- `registerRevy.ts` — `registerRevyExtensions()` registers GitHub card (`settings_integration`, `permission: 'items:view'`, `order: 10`)
- `RevyGitHubIntegrationCard.tsx` — shows connection count via `fetchInstallations(workspaceId)`; CTA links to `/installations`

Call `registerRevyExtensions()` from `main.tsx` before render. `/settings/integrations` maps `getExtensions('settings_integration')` into a grid.

**Files:** `frontend/src/platform/extensions/slots.ts`, `registry.ts`, `registerRevy.ts`, `frontend/src/features/installations/RevyGitHubIntegrationCard.tsx`, `frontend/src/features/settings/pages/IntegrationsSettingsPage.tsx`, `frontend/src/main.tsx`, tests `registry.test.ts`

**Deliverable:** `cd frontend && npm test -- --run registry IntegrationsSettingsPage RevyGitHubIntegrationCard` — green.

---

## W2.6 — Settings sidebar workspace links + router

**What:** `SettingsSidebar` — enable Workspace group `NavLink`s: `settings.nav.workspace`, `settings.nav.team`, `settings.nav.integrations`. Billing/danger: no links.

**Router tree** (extends W1):

```text
/settings → AppShellLayout → SettingsLayout
  index        → Navigate /settings/profile
  profile      → ProfileSettingsPage          (W1)
  security     → SecuritySettingsPage       (W1)
  appearance   → AppearanceSettingsPage     (W1)
  workspace    → RequirePermission admin:users → WorkspaceSettingsPage
  team         → TeamSettingsPage
  integrations → IntegrationsSettingsPage
```

**Files:** `frontend/src/features/settings/layout/SettingsSidebar.tsx`, `frontend/src/lib/routerInstance.tsx`, `frontend/src/i18n/locales/en.json`, `lv.json`

**Deliverable:** `cd frontend && npm run lint && npm run build` — green; manual: Workspace links visible; billing/danger absent; operator can open team read-only.

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest tests/unit/test_audit_model.py tests/unit/test_audit_service.py tests/unit/test_workspaces.py tests/unit/test_memberships.py tests/unit/test_invitations.py -q
```

**Phase gate** (from `frontend/`):

```bash
npm run lint && npm test -- --run WorkspaceSettingsPage TeamSettingsPage MembersTable InvitationsTable InviteMemberForm PermissionsMatrix registry IntegrationsSettingsPage RevyGitHubIntegrationCard settings && npm run build
```

**Deploy:** `alembic upgrade head` on target DB after W2.1.

**Next:** [SAAS_BASE_W3_EXECUTION.md](./SAAS_BASE_W3_EXECUTION.md)
