# docs/saas-base/waves/SAAS_BASE_W3_EXECUTION.md

# W3 — Dashboard (execution)

Wave **W3** of [`SAAS_BASE_W3_DASHBOARD_GENERAL_PLAN.md`](../SAAS_BASE_W3_DASHBOARD_GENERAL_PLAN.md). Baseline: [`SETTINGS_IA.md`](../SETTINGS_IA.md) § Extension registry, [`SAAS_BASE_FINDINGS.md`](../SAAS_BASE_FINDINGS.md) § Dashboard. **Depends on W0 (shell), W1 (profile), W2 (`api_audit` + mutation writes).** **W3 only.**

**Goal:** Workspace-aware dashboard with extension registry, wave-aware checklist, audit-lite activity, product widgets.

**Authority:** `internal-docs/starter-pack/docs/frontend/patterns/data-patterns.md`, `backend/AUDIT.md`.

## Decisions locked for W3

- **Finalize** `frontend/src/platform/extensions/` started in W2 — add `dashboard_widget` slot, `useExtensions(slot)`, `WidgetErrorBoundary`; keep `settings_integration` from W2 unchanged.
- **Extension contract** (`ExtensionDefinition`): `{ id, slot, order, permission?, component, minPlan? }` — `minPlan` ignored until W4; duplicate `id` throws at register time.
- **Widget rendering:** filter extensions by `hasPermission()`; wrap each in `WidgetErrorBoundary` (isolate product failures).
- **Setup checklist:** step registry `{ id, labelKey, isComplete(me, ctx), href?, available }` — **never** show incomplete/failed state when `available === false` (hide step entirely).
- **Default steps** (all `available: true` after W1/W2 ship):

  | Step id | `available` | `isComplete` (summary) | `href` |
  |---------|-------------|------------------------|--------|
  | `complete_profile` | always | `user.full_name` trimmed + `status === 'active'` | `/settings/profile` |
  | `invite_teammate` | `admin:users` | workspace member count > 1 (from members API) | `/settings/team` |
  | `connect_integration` | always | installations count > 0 | `/installations` |
  | `setup_billing` | **`false` until W4** | — | — |

- **Billing step:** `available: false` in W3 — not rendered (not red/X).
- **Audit read API:** `GET /api/v1/workspaces/{workspace_id}/audit` — cursor paginated; `items:view` + `require_same_workspace`; filter `workspace_id = path`; order `(created_at DESC, id DESC)`; default `limit=10` for widget, max 100.
- **`AuditListItem`:** `id`, `created_at`, `action`, `resource_type`, `resource_id`, `actor_user_id`, `actor_email`, `metadata` (pass through JSONB; cap serialized size server-side if > 4KB → `{}` for list responses).
- **No impersonator field** in list response until W7.
- **Dashboard layout order:** Welcome → Setup checklist (if any incomplete available steps) → Quick actions → Recent activity → `dashboard_widget` grid.
- **Revy:** `installations-summary` widget in `registerRevyExtensions()` (`dashboard_widget`, `items:view`, `order: 20`).
- **Plan summary:** do **not** register `plan-summary` until W4 (no placeholder card in W3).
- **No workspace selected:** show empty state (same pattern as `InstallationsPage` `noWorkspace`); hide workspace-scoped widgets.
- TanStack Query for audit + checklist context fetches; invalidate on workspace switch (`user.workspace_id`).
- EN+LV; unit tests only.

## Out of scope for W3

- Plan summary widget/data → **W4**
- Full activity feed page → **reject**
- Platform KPIs / `/admin/dashboard` → **W5**
- Platform-wide audit search → **W5**

---

## W3.1 — Workspace audit read API

**What:** `list_workspace_audit(session, workspace_id, params) → CursorResponse[AuditListItem]`; join `users` for `actor_email`. Route `GET /api/v1/workspaces/{workspace_id}/audit`.

| | |
|--|--|
| **Permission** | `items:view` + `require_same_workspace` |
| **Query** | `workspace_id` match; `ORDER BY created_at DESC, id DESC` |
| **Response** | `SuccessResponse[CursorResponse[AuditListItem]]` |

**Files:** `backend/app/api/v1/workspaces/audit.py`, `backend/app/api/v1/workspaces/__init__.py` (register router), `backend/app/services/audit_service.py` (add `list_workspace_audit`), `backend/app/schemas/audit.py` (extend with `AuditListItem`), `backend/tests/unit/test_audit_service.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_audit_service.py -q` — green including list/filter/cursor cases.

---

## W3.2 — Extension registry finalize + dashboard layout

**What:** Extend W2 `registry.ts`:

- `types.ts` — `ExtensionDefinition`, `ExtensionSlot`
- `registerExtension()` — duplicate `id` throws
- `getExtensions(slot)` — sorted by `order`
- `useExtensions(slot)` — filters by `useAuth()` role + `hasPermission()`
- `WidgetErrorBoundary.tsx` — catch render errors, show `dashboard.widgetError` i18n

`DashboardGrid.tsx` — responsive grid (`grid-cols-1 md:grid-cols-2`); `DashboardPage` composes layout sections per locked order; replaces stub welcome-only page.

**Files:** `frontend/src/platform/extensions/types.ts`, `registry.ts`, `hooks.ts`, `WidgetErrorBoundary.tsx`, `frontend/src/features/dashboard/layout/DashboardGrid.tsx`, `frontend/src/features/dashboard/pages/DashboardPage.tsx`, `registry.test.ts` (extend)

**Deliverable:** `cd frontend && npm test -- --run registry DashboardPage WidgetErrorBoundary` — green.

---

## W3.3 — Setup checklist widget

**What:** `checklistSteps.ts` — exported step registry + `evaluateChecklist(me, ctx)` where `ctx` includes `{ workspaceId, memberCount, installationCount }` from TanStack queries. `SetupChecklistWidget` — renders only steps with `available === true` and `!isComplete`; links via `react-router` `Link`; progress count i18n.

**Context loading:** `useChecklistContext()` hook — fetches member count (W0 members API, first page `items.length` or total if small) + installations count when `workspaceId` set.

**Files:** `frontend/src/features/dashboard/checklistSteps.ts`, `frontend/src/features/dashboard/hooks.ts`, `frontend/src/features/dashboard/widgets/SetupChecklistWidget.tsx`, `checklistSteps.test.ts`, `SetupChecklistWidget.test.tsx`, i18n `dashboard.checklist.*` EN+LV

**Deliverable:** `cd frontend && npm test -- --run SetupChecklistWidget checklistSteps` — green.

---

## W3.4 — Welcome + quick actions widgets

**What:**

| Widget | Content |
|--------|---------|
| **WelcomeWidget** | Active workspace name from `MeMembership`; greeting `user.full_name` fallback email; no-workspace empty state |
| **QuickActionsWidget** | Links (min 44px): Settings (`/settings/profile`), Installations (`/installations`); **admin only:** Invite teammate (`/settings/team`) |

**Files:** `frontend/src/features/dashboard/widgets/WelcomeWidget.tsx`, `QuickActionsWidget.tsx`, tests, i18n `dashboard.welcome.*`, `dashboard.quickActions.*` EN+LV

**Deliverable:** `cd frontend && npm test -- --run WelcomeWidget QuickActionsWidget` — green.

---

## W3.5 — Audit-lite activity widget

**What:** `RecentActivityWidget` — `useWorkspaceAudit(workspaceId, { limit: 10 })` TanStack Query on W3.1 API; map `action` → `dashboard.activity.{action}` i18n keys; relative time via `@/lib/date` `formatRelative()`; empty state `dashboard.activity.empty`.

**Files:** `frontend/src/features/dashboard/api.ts`, `frontend/src/features/dashboard/hooks.ts`, `frontend/src/features/dashboard/widgets/RecentActivityWidget.tsx`, `RecentActivityWidget.test.tsx`, i18n `dashboard.activity.*` EN+LV (all W2 audit actions)

**Deliverable:** `cd frontend && npm test -- --run RecentActivityWidget` — green.

---

## W3.6 — Revy installations widget + bootstrap registration

**What:** `InstallationsSummaryWidget` — installation count + status summary + link to `/installations`. Extend `registerRevyExtensions()` in `registerRevy.ts`:

```ts
registerExtension({ id: 'installations-summary', slot: 'dashboard_widget', order: 20, permission: 'items:view', component: InstallationsSummaryWidget })
```

(Keep W2 `settings_integration` GitHub card registration in same function.)

**Files:** `frontend/src/features/installations/InstallationsSummaryWidget.tsx`, `frontend/src/platform/extensions/registerRevy.ts`, `InstallationsSummaryWidget.test.tsx`

**Deliverable:** `cd frontend && npm test -- --run InstallationsSummaryWidget registry` — green.

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest tests/unit/test_audit_service.py -q
```

**Phase gate** (from `frontend/`):

```bash
npm run lint && npm test -- --run registry WidgetErrorBoundary DashboardPage checklistSteps SetupChecklistWidget WelcomeWidget QuickActionsWidget RecentActivityWidget InstallationsSummaryWidget settings && npm run build
```

**Deploy:** none.

**Next:** [SAAS_BASE_W4_EXECUTION.md](./SAAS_BASE_W4_EXECUTION.md)
