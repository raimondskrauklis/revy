# docs/saas-base/waves/SAAS_BASE_W6_EXECUTION.md

# W6 — Account lifecycle (execution)

Wave **W6** of [`SAAS_BASE_W6_LIFECYCLE_GENERAL_PLAN.md`](../SAAS_BASE_W6_LIFECYCLE_GENERAL_PLAN.md). Baseline: [`SAAS_BASE_FINDINGS.md`](../SAAS_BASE_FINDINGS.md) § Account lifecycle, § deferred notifications. **Depends on W1 (profile), W2 (membership APIs + `record_audit`), W4 (paid-workspace delete guard).** **W6 only.**

**Goal:** Danger zone — leave workspace, delete workspace, export data, delete account.

**Authority:** `internal-docs/starter-pack/docs/backend/ACCOUNT_LIFECYCLE.md`.

## Decisions locked for W6

- **No email notifications** — deferred program; UI shows confirmation copy only.
- **Status transitions (no hard-delete rows):** extend enums via migration — `UserStatus.deleted`, `WorkspaceStatus.deleted`; reject `deleted` users in `get_current_user` (`ForbiddenError`, `error_code=account_deleted`).
- **Leave workspace:** `POST /api/v1/workspaces/{workspace_id}/leave` — removes **current user** membership; reuses W0 last-admin guard (`error_code=last_workspace_admin`).
- **Delete workspace:** `DELETE /api/v1/workspaces/{workspace_id}` — `admin:users`; body `{ "confirm_slug": "<workspace.slug>" }`; set `workspaces.status = deleted`; remove all `workspace_memberships`; **block** when `effective_plan(workspace) == "pro"` and `stripe_customer_id` is set (`error_code=subscription_active` — cancel via Portal first, W4).
- **Delete account:** `DELETE /api/v1/me` — body `{ "confirm_email": "<user.email>" }`; `users.status = deleted`; anonymize email `deleted+<uuid>@revy.invalid`; remove all memberships; **block** if user is sole `admin` of any workspace (`error_code=sole_workspace_admin`); **block** `platform_role=super_admin` self-delete (`error_code=platform_admin_protected`). Keycloak user **not** deleted in W6 (document in UI).
- **Data export:** `data_export_jobs` table + Celery task in `app/workers/export_tasks.py`; one active job per user (`pending`|`processing`).

  | Method | Path | Purpose |
  |--------|------|---------|
  | `POST` | `/api/v1/me/export` | Create job → `{ "job_id": "..." }` |
  | `GET` | `/api/v1/me/export/{job_id}` | Poll `{ status, created_at, completed_at, expires_at }` |
  | `GET` | `/api/v1/me/export/{job_id}/download` | Stream ZIP when `status=completed` (owner only) |

- **Export artifact:** JSON bundle (user profile, memberships, workspace names) → ZIP on disk at `EXPORT_STORAGE_PATH` (dev) or configured path; `expires_at` = `completed_at + EXPORT_TTL_DAYS` (default 7).
- **Export job statuses:** `pending` → `processing` → `completed` \| `failed`.
- **Audit** (same transaction as mutation via W2 `record_audit`): `workspace.left`, `workspace.deleted`, `user.export_requested`, `user.deleted`.
- **Settings UI:** `/settings/danger` — any member; export + leave + delete account; delete workspace section **admin only** (`admin:users`).
- **Confirmation UX:** type workspace **slug** or account **email** in `ConfirmDestructiveModal`; logout + redirect after account delete.
- Sidebar: enable `settings.nav.danger` under Workspace group.
- EN+LV; service-layer unit tests only.

## Out of scope for W6

- Email export-ready notification → **deferred program**
- GDPR legal hold / retention UI → ACCOUNT_LIFECYCLE doc only
- Keycloak user deletion → manual / future program
- Impersonation interactions → **W7** (`impersonator_user_id` on audit already)

---

## W6.1 — Lifecycle enums + `data_export_jobs` migration

**What:** Hand-written Alembic:

1. `ALTER TYPE user_status ADD VALUE 'deleted'` (if not exists pattern per repo migrations)
2. `ALTER TYPE workspace_status ADD VALUE 'deleted'`
3. Table `data_export_jobs` — `id` UUID PK, `user_id` FK → `users`, `status` (text or enum), `storage_key`, `error_message`, `file_size_bytes`, `expires_at`, `created_at`, `updated_at`, `completed_at`

Update `enums.py` + ORM `DataExportJobORM`. Config: `export_storage_path`, `export_ttl_days` in `config.py`.

**Files:** `backend/alembic/versions/YYYY_MM_DD_HHMM_NNNN_lifecycle_export_jobs.py`, `backend/app/constants/enums.py` (`ExportJobStatus`), `backend/app/models/data_export_job.py`, `backend/app/models/__init__.py`, `backend/app/core/config.py`, `backend/.env.example`, `backend/tests/unit/test_data_export_model.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_data_export_model.py -q` — green.

**LOOP pause:** `alembic upgrade head` before W6.2+.

---

## W6.2 — Export job service + Celery task

**What:** `services/data_export.py` — `create_export_job`, `build_export_payload`, `mark_completed` / `mark_failed`. `workers/export_tasks.py` — `run_data_export_job(job_id)`; register route in `celery_app.py` (`queue: default` or `maintenance`). Task writes ZIP to `EXPORT_STORAGE_PATH/{job_id}.zip`.

**Files:** `backend/app/services/data_export.py`, `backend/app/workers/export_tasks.py`, `backend/app/workers/celery_app.py`, `backend/tests/unit/test_data_export_service.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_data_export_service.py -q` — green.

---

## W6.3 — Lifecycle APIs + audit wiring

**What:** `services/account_lifecycle.py` — `leave_workspace`, `delete_workspace`, `delete_account`; call `record_audit` in same transaction. Routes:

| Method | Path | Permission |
|--------|------|------------|
| `POST` | `/api/v1/workspaces/{workspace_id}/leave` | member + `require_same_workspace` |
| `DELETE` | `/api/v1/workspaces/{workspace_id}` | `admin:users` + confirm slug body |
| `DELETE` | `/api/v1/me` | authenticated + confirm email body |
| `POST` | `/api/v1/me/export` | authenticated `active` |
| `GET` | `/api/v1/me/export/{job_id}` | owner only |
| `GET` | `/api/v1/me/export/{job_id}/download` | owner only, `completed` + not expired |

Extend `get_current_user` to reject `UserStatus.deleted`. Register `lifecycle.py` under workspaces router + extend `me.py`.

**Files:** `backend/app/services/account_lifecycle.py`, `backend/app/api/v1/workspaces/lifecycle.py`, `backend/app/api/v1/workspaces/__init__.py`, `backend/app/api/v1/me.py`, `backend/app/schemas/lifecycle.py`, `backend/app/core/auth.py`, `backend/tests/unit/test_account_lifecycle.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_account_lifecycle.py tests/unit/test_audit_service.py -q` — green (audit rows asserted).

---

## W6.4 — Danger zone settings UI

**What:** `/settings/danger` — sections:

| Section | Who | UX |
|---------|-----|-----|
| **Export data** | all | Request export → poll status → download link when ready |
| **Leave workspace** | all | Confirm modal → `POST leave` |
| **Delete workspace** | admin | Type slug confirm → `DELETE workspace` |
| **Delete account** | all | Type email confirm → `DELETE /me` → `logout()` |

`ConfirmDestructiveModal` — reusable typed confirmation + danger styling.

**Files:** `frontend/src/features/settings/pages/DangerZonePage.tsx`, `frontend/src/features/settings/components/ConfirmDestructiveModal.tsx`, `frontend/src/features/settings/api.ts`, `frontend/src/features/settings/hooks.ts`, tests, i18n `settings.danger.*` + `errors.subscription_active`, `errors.sole_workspace_admin`, `errors.platform_admin_protected` EN+LV

**Deliverable:** `cd frontend && npm test -- --run DangerZonePage ConfirmDestructiveModal` — green.

---

## W6.5 — Settings sidebar danger link + router

**What:** Enable `settings.nav.danger` in `SettingsSidebar`. Route:

```text
settings/danger → DangerZonePage   (any member; admin-only sections inside page)
```

Extend W1/W2/W4 settings router tree.

**Files:** `frontend/src/features/settings/layout/SettingsSidebar.tsx`, `frontend/src/lib/routerInstance.tsx`, i18n nav keys

**Deliverable:** `cd frontend && npm run build` — green; manual: danger link visible; billing link still present (W4).

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest tests/unit/test_data_export_model.py tests/unit/test_data_export_service.py tests/unit/test_account_lifecycle.py tests/unit/test_audit_service.py -q
```

**Phase gate** (from `frontend/`):

```bash
npm run lint && npm test -- --run DangerZonePage ConfirmDestructiveModal settings && npm run build
```

**Human gate:** dev export round-trip — `POST /me/export` → Celery worker running → download ZIP from `/settings/danger`.

**Deploy:** `alembic upgrade head`; set `EXPORT_STORAGE_PATH` on API/worker droplets; ensure Celery worker consumes export task queue.

**Next:** [SAAS_BASE_W7_EXECUTION.md](./SAAS_BASE_W7_EXECUTION.md)
