# docs/saas-base/waves/SAAS_BASE_W8_EXECUTION.md

# W8 — Platform hardening & ship readiness (execution)

Wave **W8** of [`SAAS_BASE_W8_PLATFORM_HARDENING_GENERAL_PLAN.md`](../SAAS_BASE_W8_PLATFORM_HARDENING_GENERAL_PLAN.md). Baseline: post-W7 platform review + [`SAAS_BASE_FINDINGS.md`](../SAAS_BASE_FINDINGS.md). **Depends on W0–W7.** **W8 only.**

**Goal:** Close permission leaks, data-accuracy corners, impersonation holes, ops gaps, and sync all platform docs/runbooks with shipped code. **No new product features.**

**Authority:** [SETTINGS_IA.md](../SETTINGS_IA.md), `docs/starter-pack/DEV_BOOTSTRAP.md`, `docs/utils/STRIPE_BILLING_SETUP.md`, `deploy/env-examples/`, `AGENTS.md`.

## Decisions locked for W8

- **Read-only plan for all members:** `GET /me` includes `workspace_plan: "free" | "pro" | null` for the active workspace (from `workspaces.plan` join). Billing admin API (`GET .../billing`) remains **admin-only** for Stripe flags + checkout/portal actions.
- **Frontend plan reads:** dashboard extensions, checklist, `PlanSummaryWidget` use `user.workspace_plan` from `/me` — **never** call billing status API unless user has `admin:users`.
- **Settings nav honesty:** sidebar links filtered by `hasPermission` — same rules as `RequirePermission` on routes (workspace + billing admin-only; team/integrations/danger any member).
- **Suspended tenant UX:** `/me` memberships exclude `workspaces.status != active`. New route `/workspace-suspended` (status gate). API `workspace_suspended` → FE maps to gate via global error handler or auth refetch.
- **Impersonation:** `POST /workspaces/{id}/leave` added to deny-list; all lifecycle `record_audit` calls pass `impersonator_user_id` when set.
- **Member count:** `GET /api/v1/workspaces/{id}/members/count` → `{ "count": N }` (any member); checklist uses this instead of first-page length.
- **Invitations:** `list_invitations` excludes rows where `status=pending` AND `expires_at <= now()` (or auto-set `expired` on read — pick one, document in AUDIT/invitations service).
- **Admin KPIs:** `workspaces_total` counts only `active` + `suspended` (excludes `deleted`); optional `workspaces_deleted` field on `AdminKpisResponse` if useful for ops.
- **Orphan Stripe webhooks:** subscription/customer events with no matching workspace → **log warning + return 200** (ack, no DB plan change). Do not raise `BillingWebhookError` for orphan customer (findings edge case #8). Checkout with valid metadata but missing workspace → still retry (500).
- **Doc sync:** one authoritative execution tree — delete `docs/saas-base/waves/w0/` … `w7/` duplicate copies after W8.6.
- EN+LV; service-layer unit tests only.

## Out of scope for W8

- Notifications, API keys, file uploads, in-app user directory → **deferred program**
- Impersonation session TTL cron → follow-up
- In-app changelog UI → defer unless trivial `<1h` wiring; else document “file reserved” in doc sync
- New Alembic migrations unless strictly required (prefer query/logic fixes)

---

## W8.1 — Read-only plan on `/me` + tenant UX

**What:**

| Change | Detail |
|--------|--------|
| **`MeResponse`** | Add `workspace_plan: str \| null` (effective plan for active workspace) |
| **`build_me_response`** | Join active workspace; set plan via `effective_plan()`; filter memberships to `WorkspaceStatus.active` only |
| **FE `MeUser`** | `workspace_plan` field; checklist + `useExtensions` use it for `minPlan` |
| **`useBillingStatus`** | `enabled: Boolean(workspaceId) && canManageBilling` |
| **`SettingsSidebar`** | Filter `WORKSPACE_LINKS` by permission (workspace/billing → `admin:users`) |
| **Status route** | `/workspace-suspended` + i18n; handle `workspace_suspended` in API error toast → navigate or show gate |

**Files:** `backend/app/schemas/me.py`, `backend/app/services/users.py`, `backend/app/api/v1/me.py`, `frontend/src/lib/me.ts`, `frontend/src/platform/extensions/hooks.ts`, `frontend/src/features/dashboard/hooks.ts`, `frontend/src/features/dashboard/widgets/PlanSummaryWidget.tsx`, `frontend/src/features/settings/layout/SettingsSidebar.tsx`, `frontend/src/lib/routerInstance.tsx`, `frontend/src/shared/errors/toasts.ts` (optional redirect), tests, i18n EN+LV

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_users_me.py tests/unit/test_me_routes.py -q` && `cd frontend && npm test -- --run SettingsSidebar useExtensions SetupChecklistWidget PlanSummaryWidget` — green; manual: viewer dashboard no billing 403.

---

## W8.2 — Impersonation closure + error i18n

**What:**

| Change | Detail |
|--------|--------|
| **Leave deny-list** | `require_impersonation_allowed()` on `POST .../leave` |
| **Audit** | `leave_workspace` accepts `impersonator_user_id`; audit all lifecycle mutations consistently |
| **i18n** | `errors.workspace_suspended`, `errors.impersonation_active`, `errors.impersonation_forbidden`, `errors.impersonation_restricted`, `errors.impersonation_invalid`, `errors.impersonation_not_active` EN+LV |
| **Auth** | `UserStatus.suspended` API responses include `error_code=account_suspended` (optional FE gate parity) |

**Files:** `backend/app/api/v1/workspaces/lifecycle.py`, `backend/app/services/account_lifecycle.py`, `backend/app/core/auth.py`, `backend/tests/unit/test_account_lifecycle.py`, `backend/tests/unit/test_auth_impersonation.py`, `frontend/src/i18n/locales/en.json`, `lv.json`, tests

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_account_lifecycle.py tests/unit/test_auth_impersonation.py -q` — green; assert leave blocked while impersonating.

---

## W8.3 — Data accuracy (KPIs, invitations, member count)

**What:**

| API / surface | Fix |
|---------------|-----|
| **`GET /admin/kpis`** | `workspaces_total` = active + suspended only; add `workspaces_deleted` count |
| **`list_invitations`** | Exclude expired pending invites from list (or mark expired) |
| **`GET /workspaces/{id}/members/count`** | `{ count: int }` — any workspace member |
| **Checklist** | `useChecklistContext` uses count endpoint |
| **FE invitations** | Optional `expired` badge if any stale rows remain visible |

**Files:** `backend/app/services/admin_kpis.py`, `backend/app/schemas/admin.py`, `backend/app/services/invitations.py`, `backend/app/api/v1/workspaces/members.py` (or new count route), `backend/app/schemas/memberships.py`, `frontend/src/features/dashboard/hooks.ts`, `frontend/src/features/settings/api.ts`, tests, i18n

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_admin_kpis.py tests/unit/test_invitations.py tests/unit/test_members_count.py -q` && `cd frontend && npm test -- --run checklistSteps InvitationsTable` — green.

---

## W8.4 — Billing webhook policy + plan semantics

**What:**

- **`apply_subscription_event`:** orphan customer/subscription (no workspace row) → log + return without error (200 at handler). Missing workspace on **checkout.session.completed** with valid metadata → keep `BillingWebhookError` (retry).
- **Runbook:** document `past_due` → `pro` in `docs/utils/STRIPE_BILLING_SETUP.md`; document orphan vs retry policy.
- **`plan_gates.py`:** module docstring listing gated features (`installations.create` today); pattern for future gates.

**Files:** `backend/app/services/billing.py`, `backend/tests/unit/test_billing_service.py`, `docs/utils/STRIPE_BILLING_SETUP.md`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_billing_service.py tests/unit/test_stripe_webhook.py -q` — green.

---

## W8.5 — Ops deploy parity + staging verification

**What:**

| Artifact | Content |
|----------|---------|
| **`deploy/env-examples/backend.env.production.example`** | `EXPORT_STORAGE_PATH`, `EXPORT_TTL_DAYS`; comment Celery `maintenance` queue |
| **`docs/starter-pack/DEV_BOOTSTRAP.md`** | Migrations `0008`–`0009`; local export path; `celery -A app.workers.celery_app worker -Q maintenance,default` |
| **`docs/saas-base/STAGING_VERIFICATION.md`** | Human gates from W4–W7 as checkbox matrix (Stripe e2e, super_admin bootstrap, export round-trip, impersonation review) |
| **`docs/saas-base/OPS.md`** | Short ops index: export worker, Stripe webhook, bootstrap super_admin pointers |

**Files:** deploy examples, `DEV_BOOTSTRAP.md`, new `docs/saas-base/STAGING_VERIFICATION.md`, new `docs/saas-base/OPS.md`

**Deliverable:** `grep -r EXPORT_STORAGE_PATH deploy/env-examples/` succeeds; `test -f docs/saas-base/STAGING_VERIFICATION.md`.

**Human gate:** run staging verification checklist before prod SaaS base sign-off (LOOP may ship code; checklist signed separately).

---

## W8.6 — Platform-wide doc sync

**What:** Reconcile **all** docs with shipped W0–W8. Adjust runbooks as needed — they were scaffold baselines.

| Doc | Change |
|-----|--------|
| [`SAAS_BASE_FINDINGS.md`](../SAAS_BASE_FINDINGS.md) | Update “what exists” tables (no stubs); add W8; program status → complete after W8 ships; resolve impersonation TTL vs W7 defer note |
| [`SAAS_BASE_W*_GENERAL_PLAN.md`](../) | Status → done (W0–W7) / W8 pending→done; remove “Not started” on W4 etc. |
| [`README.md`](../README.md) | W8 row; program complete **after W8** |
| [`waves/README.md`](./README.md) | W8 row + SHA on ship |
| [`SETTINGS_IA.md`](../SETTINGS_IA.md) | Permission-aware nav; `workspace_plan` on `/me`; resolve `settings_nav` slot (implement or remove from doc) |
| [`AGENTS.md`](../../AGENTS.md) | SaaS base index: W8, OPS, STAGING_VERIFICATION, fast-start strip |
| [`docs/starter-pack/README.md`](../../starter-pack/README.md) | Pointer to SaaS base program + prerequisite note |
| [`SAAS_BASE_W7_EXECUTION.md`](./SAAS_BASE_W7_EXECUTION.md) | Remove “Final wave” — point to W8 |
| **Fast-start** | Create [`FAST_START_STRIP_LIST.md`](../FAST_START_STRIP_LIST.md) — product folders, env keys, nav to drop for clone |
| **Dedupe** | Delete `waves/w0/` … `waves/w7/` duplicate execution files (keep flat `waves/SAAS_BASE_W*_EXECUTION.md` only) |
| **`internal-docs/`** | Note in README for contributors to sync SETTINGS_IA mirror |
| **`frontend/src/data/changelog.json`** | Add W8 entry on ship |

**Deliverable:**

```bash
# No duplicate nested execution trees
! test -d docs/saas-base/waves/w0
# Findings mentions W8 and shipped dashboard/settings
grep -q "W8" docs/saas-base/SAAS_BASE_FINDINGS.md
grep -q "workspace_plan" docs/saas-base/SETTINGS_IA.md
python -m json.tool frontend/src/data/changelog.json > /dev/null
cd frontend && npm run build
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest \
  tests/unit/test_users_me.py \
  tests/unit/test_me_routes.py \
  tests/unit/test_account_lifecycle.py \
  tests/unit/test_auth_impersonation.py \
  tests/unit/test_admin_kpis.py \
  tests/unit/test_invitations.py \
  tests/unit/test_members_count.py \
  tests/unit/test_billing_service.py \
  tests/unit/test_stripe_webhook.py \
  -q
```

**Phase gate** (from `frontend/`):

```bash
npm run lint && npm test -- --run SettingsSidebar useExtensions SetupChecklistWidget PlanSummaryWidget checklistSteps InvitationsTable ImpersonationBanner admin settings && npm run build
```

**Human gate:** [`STAGING_VERIFICATION.md`](../STAGING_VERIFICATION.md) executed on staging before production SaaS base sign-off.

**Deploy:** no new migrations expected; ensure `alembic upgrade head` through `0009` on all environments; export worker on `maintenance` queue.

**Next:** none — SaaS base W0–W8 complete after W8 ships.
