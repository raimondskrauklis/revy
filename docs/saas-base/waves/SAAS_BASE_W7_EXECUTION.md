# docs/saas-base/waves/SAAS_BASE_W7_EXECUTION.md

# W7 — Impersonation (execution)

Wave **W7** of [`SAAS_BASE_W7_IMPERSONATION_GENERAL_PLAN.md`](../SAAS_BASE_W7_IMPERSONATION_GENERAL_PLAN.md). Baseline: [`SAAS_BASE_FINDINGS.md`](../SAAS_BASE_FINDINGS.md) Q18, § Audit table. **Depends on W2 (`record_audit` + `impersonator_user_id`), W5 (workspace detail UI), W6 (lifecycle deny-list).** **W7 only** (followed by **W8** hardening).

**Goal:** Super-admin impersonation with server-side session, audit trail, SPA banner, safe route deny list.

## Decisions locked for W7

- Keycloak session **unchanged** — JWT `sub` remains the real `super_admin`; impersonation is **app-layer only**.
- **`CurrentUser`:** `actor_user_id` (real PG user, always the super_admin), `impersonated_user_id: UUID | None`, `effective_user_id` property → `impersonated_user_id or actor_user_id`. Workspace role / `X-Workspace-Id` resolution uses **effective** user's memberships; `platform_role` checks use **actor** only.
- **Storage:** `impersonation_sessions` — `id`, `actor_user_id`, `target_user_id`, `reason` TEXT NOT NULL, `started_at`, `ended_at` NULL; **one active session per actor** (partial unique index `ended_at IS NULL`).
- **Start API:** `POST /api/v1/admin/impersonation/start` body `{ "user_id": UUID, "reason": string }` — `reason` min 10 chars (mandatory); `require_super_admin()`; reject if actor already impersonating (`error_code=impersonation_active`).
- **Stop API:** `POST /api/v1/admin/impersonation/stop` — ends active session for actor.
- **Status API:** `GET /api/v1/admin/impersonation/active` → `{ active, target_user_id?, target_email?, reason?, started_at? }`.
- **Target rules:** target must be `UserStatus.active`; **cannot** impersonate `platform_role=super_admin`; cannot impersonate `deleted` / `suspended` / `pending_*` users.
- **Admin member picker:** `GET /api/v1/admin/workspaces/{workspace_id}/members` — cursor list for impersonation target selection on workspace detail (super_admin only; cross-tenant).
- **`GET /me`:** include `impersonation: { active, actor_user_id, target_user_id, target_email, reason } | null` for banner; effective profile fields from target when active.
- **Audit:** `platform.impersonation.started`, `platform.impersonation.stopped` on session changes; **all mutation audits** pass `impersonator_user_id=actor_user_id` when impersonating (W2 `record_audit` param).
- **API deny-list while impersonating** (`ForbiddenError`, `error_code=impersonation_restricted`):
  - Any `/api/v1/admin/*` (including start/stop except `POST .../stop`)
  - `DELETE /api/v1/me`, `POST /api/v1/me/export`
  - `DELETE /api/v1/workspaces/{id}`, `POST .../billing/checkout-session`, `POST .../billing/portal-session`
- **FE deny-list:** block `/admin/*` routes when `me.impersonation.active`; show `ImpersonationBanner` in `AppShellLayout`; Stop → `POST stop` + `refetchUser()` + navigate `/dashboard`.
- **Workspace detail:** member table with **Impersonate** per row (reason modal) → start API → redirect `/dashboard`.
- EN+LV; service-layer unit tests only.

### ADR — server-side impersonation

```text
Context: Support needs to reproduce tenant issues without password sharing.
Decision: PostgreSQL impersonation_sessions + CurrentUser effective_user_id;
          KC token unchanged; mandatory reason; audit impersonator_user_id on all writes.
Consequences: Admin routes blocked while impersonating; destructive/billing APIs blocked.
```

## Out of scope for W7

- KC token exchange / forged JWT → **reject**
- Auto-expire TTL / cron cleanup → optional follow-up (manual stop required v1)
- Notify impersonated user → **deferred program**

---

## W7.1 — `impersonation_sessions` migration + ORM

**What:** Hand-written Alembic table + partial unique index on `actor_user_id WHERE ended_at IS NULL`. `ImpersonationSessionORM`; export from `models/__init__.py`.

**Files:** `backend/alembic/versions/YYYY_MM_DD_HHMM_NNNN_impersonation_sessions.py`, `backend/app/models/impersonation_session.py`, `backend/app/models/__init__.py`, `backend/tests/unit/test_impersonation_model.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_impersonation_model.py -q` — green.

**LOOP pause:** `alembic upgrade head` before W7.2+.

---

## W7.2 — Impersonation service + admin APIs

**What:** `start_impersonation`, `stop_impersonation`, `get_active_session`, `list_workspace_members_for_admin`. Routes under `admin/impersonation.py` + `admin/workspaces.py` (members list). Audit on start/stop.

| Method | Path |
|--------|------|
| `POST` | `/api/v1/admin/impersonation/start` |
| `POST` | `/api/v1/admin/impersonation/stop` |
| `GET` | `/api/v1/admin/impersonation/active` |
| `GET` | `/api/v1/admin/workspaces/{workspace_id}/members` |

**Files:** `backend/app/services/impersonation.py`, `backend/app/api/v1/admin/impersonation.py`, `backend/app/api/v1/admin/workspaces.py` (extend), `backend/app/schemas/impersonation.py`, `backend/app/api/v1/admin/__init__.py`, `backend/tests/unit/test_impersonation_service.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_impersonation_service.py -q` — green.

---

## W7.3 — `CurrentUser` + auth + audit integration

**What:**

- Load active session in `get_current_user` after actor resolution.
- Resolve workspace membership from **effective** user.
- `build_me_response` returns impersonation block + effective profile.
- `record_audit` callers pass `impersonator_user_id` from `CurrentUser` when set.
- `require_impersonation_allowed` dependency on deny-listed routes.
- `require_super_admin` uses **actor** `platform_role`, not effective user.

**Files:** `backend/app/core/auth.py`, `backend/app/schemas/me.py`, `backend/app/api/v1/me.py`, `backend/app/services/audit_service.py` (wire impersonator), deny-list on lifecycle + billing + admin routes, `backend/tests/unit/test_auth_impersonation.py`, `backend/tests/unit/test_audit_service.py` (impersonator column asserted)

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_auth_impersonation.py tests/unit/test_audit_service.py -q` — green.

---

## W7.4 — Impersonation banner + admin UI

**What:**

| Component | Behavior |
|-----------|----------|
| **`ImpersonationBanner`** | Fixed banner when `me.impersonation.active`; target email + reason snippet; Stop button |
| **`WorkspaceDetailPage`** | Members table (admin members API) + Impersonate → reason modal → start → `/dashboard` |
| **`BlockAdminWhileImpersonating`** | Wrapper on `/admin` routes — redirect `/dashboard` if impersonating |
| **`me.ts` / AuthContext** | Types + `refetchUser` after start/stop |

Mount banner in `AppShellLayout` (not `AdminLayout`).

**Files:** `frontend/src/features/admin/components/ImpersonationBanner.tsx`, `ImpersonationStartModal.tsx`, `frontend/src/features/admin/pages/WorkspaceDetailPage.tsx`, `frontend/src/components/auth/BlockAdminWhileImpersonating.tsx`, `frontend/src/components/layout/AppShellLayout.tsx`, `frontend/src/lib/me.ts`, `frontend/src/contexts/AuthContext.tsx`, `frontend/src/features/admin/api.ts`, `frontend/src/lib/routerInstance.tsx`, i18n `admin.impersonation.*` EN+LV

**Deliverable:** `cd frontend && npm test -- --run ImpersonationBanner ImpersonationStartModal BlockAdminWhileImpersonating` — green.

---

## W7.5 — Admin audit UI + impersonator column

**What:** Extend `AuditSearchPage` to show `impersonator_user_id` / email when present; filter hint in i18n. Backend `AuditListItem` adds optional `impersonator_user_id`, `impersonator_email` on platform + workspace audit list responses.

**Files:** `backend/app/schemas/audit.py`, `backend/app/services/audit_service.py`, `frontend/src/features/admin/pages/AuditSearchPage.tsx`, tests

**Deliverable:** `cd frontend && npm test -- --run AuditSearchPage` — green.

---

## W7.6 — Program doc sync (final wave)

**What:** Close SaaS base program docs after W7 ships.

| Doc | Change |
|-----|--------|
| `docs/saas-base/waves/README.md` | All waves W0–W7 status → `done` + commit SHA (phase-execution LOOP) |
| `docs/saas-base/README.md` | Program status → **complete**; next → maintenance / product slices |
| `frontend/src/data/changelog.json` | Create if missing; entry **SaaS settings & admin** (settings, team, billing, platform admin, impersonation) |

```bash
test -f frontend/src/data/changelog.json && python -m json.tool frontend/src/data/changelog.json > /dev/null
cd frontend && npm run build
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest tests/unit/test_impersonation_model.py tests/unit/test_impersonation_service.py tests/unit/test_auth_impersonation.py tests/unit/test_audit_service.py -q
```

**Phase gate** (from `frontend/`):

```bash
npm run lint && npm test -- --run ImpersonationBanner ImpersonationStartModal BlockAdminWhileImpersonating AuditSearchPage admin settings && npm run build
```

**Human gate:** security review on staging — super_admin only, mandatory reason in audit, `/admin` blocked while impersonating, stop restores actor session, impersonator visible in `/admin/audit`.

**Deploy:** `alembic upgrade head`; document impersonation policy for support staff.

**Next:** [SAAS_BASE_W8_EXECUTION.md](./SAAS_BASE_W8_EXECUTION.md)
