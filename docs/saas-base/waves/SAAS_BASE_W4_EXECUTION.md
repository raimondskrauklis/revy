# docs/saas-base/waves/SAAS_BASE_W4_EXECUTION.md

# W4 — Stripe billing (execution)

Wave **W4** of [`SAAS_BASE_W4_STRIPE_GENERAL_PLAN.md`](../SAAS_BASE_W4_STRIPE_GENERAL_PLAN.md). Baseline: [`SAAS_BASE_FINDINGS.md`](../SAAS_BASE_FINDINGS.md) Q4, Q20, § Billing. **Depends on W0 (workspace APIs), W2 (settings shell + audit writes), W3 (dashboard + extension registry).** **W4 only.**

**Goal:** Full Stripe integration — Checkout, Customer Portal, webhooks, plan gates, billing settings UI.

**Operator runbook:** [STRIPE_BILLING_SETUP.md](../../utils/STRIPE_BILLING_SETUP.md) (env, webhook URL, test-mode flow, W8 orphan policy).

**Authority:** `internal-docs/starter-pack/docs/backend/BILLING.md`, `deploy/env-examples/`.

## Decisions locked for W4

- **Billing unit:** workspace — reuse `workspaces.stripe_customer_id`, `workspaces.plan` (`String(64)`, nullable → treat `NULL` as `free`).
- **Plan tiers v1:** `free` \| `pro` only; no `subscription_status` column — Stripe is source of truth for payment state; DB holds effective plan for gating.
- **Stripe Python SDK** — add to `backend/Pipfile`; settings: `STRIPE_ENABLED` (bool, default `false`), `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_PRICE_PRO` (price ID), optional `STRIPE_CHECKOUT_SUCCESS_URL`, `STRIPE_CHECKOUT_CANCEL_URL` (fallback: `{APP_PUBLIC_URL}/settings/billing?checkout=success|cancel`).
- **FE:** optional `VITE_STRIPE_PUBLISHABLE_KEY` (Checkout redirect v1 — no Elements required).
- **When `STRIPE_ENABLED=false`:** billing mutation endpoints return `ServiceUnavailableError` (`error_code=billing_disabled`); `GET .../billing` returns `{ plan: "free", stripe_enabled: false }`; FE shows “billing not configured” copy (not an error toast).
- **Routes (workspace admin):** all require `admin:users` + `require_same_workspace`:

  | Method | Path | Purpose |
  |--------|------|---------|
  | `GET` | `/api/v1/workspaces/{workspace_id}/billing` | Current plan + `stripe_enabled` |
  | `POST` | `/api/v1/workspaces/{workspace_id}/billing/checkout-session` | Body `{ "plan": "pro" }` → `{ "url": "..." }` |
  | `POST` | `/api/v1/workspaces/{workspace_id}/billing/portal-session` | `{ "url": "..." }` (requires `stripe_customer_id`) |

- **Webhook:** `POST /api/v1/webhooks/stripe` — **no JWT**; verify signature on **raw body** (`await request.body()`); idempotent via `stripe_webhook_events` table.
- **Webhook events (handle):** `checkout.session.completed`, `customer.subscription.updated`, `customer.subscription.deleted`, `invoice.paid`, `invoice.payment_failed` — update `workspaces.plan` / `stripe_customer_id` on subscription lifecycle; invoice events → audit only in v1.
- **Idempotency table:** `stripe_webhook_events` (`event_id` TEXT PK, `event_type` TEXT, `processed_at` TIMESTAMPTZ, `created_at` TIMESTAMPTZ default `now()`).
- **Checkout metadata:** `workspace_id`, `plan` on session — webhook uses metadata to sync correct workspace.
- **Plan gating:** `app/core/plan_gates.py` — `PLAN_FEATURES` map, `effective_plan(workspace) → str`, `require_plan_feature(feature: str)` dependency; denied → `ForbiddenError` (`error_code=plan_upgrade_required`, `details={ feature, required_plan: "pro" }`).
- **Proof gate:** `POST /api/v1/workspaces/{workspace_id}/installations` (`workspaces/installations.py`) requires feature `installations.create` → **pro** plan.
- **Audit** (via W2 `record_audit`): `billing.checkout_started`, `billing.portal_opened`, `billing.subscription_updated` (include `old_plan`, `new_plan` in metadata).
- **Settings UI:** `/settings/billing` — `RequirePermission admin:users`; sidebar link enabled.
- **Dashboard:** register `plan-summary` widget (`dashboard_widget`, `minPlan` unused — always render for admin); enable checklist `setup_billing` (`available: true`, `isComplete: plan === 'pro'`, `href: /settings/billing`).
- EN+LV; **service-layer unit tests only** (`tests/unit/`).

## Out of scope for W4

- Per-seat / usage metering → **reject** v1
- Invoice PDF in-app → Stripe Portal only
- `plan_limit()` numeric quotas → **reject** v1 (boolean features only)
- Platform admin billing overrides → **W5** (Stripe Dashboard link)
- Paid workspace delete guard → **W6** (references W4 `plan` + `stripe_customer_id`)

---

## W4.1 — Billing schema migration + config

**What:** Hand-written Alembic `stripe_webhook_events`; optional index on `workspaces.stripe_customer_id` if missing. Add Stripe settings to `config.py`. Env snippets: `backend/.env.example`, `deploy/env-examples/backend.env.production.example`, `deploy/env-examples/frontend.env.local.example`. Add `stripe` to `Pipfile`.

**Files:** `backend/alembic/versions/YYYY_MM_DD_HHMM_NNNN_stripe_webhook_events.py`, `backend/app/core/config.py`, `backend/Pipfile`, `backend/.env.example`, `deploy/env-examples/backend.env.production.example`, `deploy/env-examples/frontend.env.local.example`, `backend/tests/unit/test_billing_config.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_billing_config.py -q` — green.

**LOOP pause:** `pipenv install` + `alembic upgrade head` on dev DB before W4.2+.

---

## W4.2 — Billing service + Stripe client wrapper

**What:** `integrations/stripe_client.py` — protocol + real `StripeClient` + `NullStripeClient` when disabled. `services/billing.py`:

- `get_billing_status(session, workspace_id) → BillingStatus`
- `create_checkout_session(...)` — create/reuse Stripe customer; set metadata
- `create_portal_session(...)`
- `apply_subscription_event(session, event)` — map `STRIPE_PRICE_PRO` → `pro`; deletion → `free`
- `effective_plan(workspace) → "free"|"pro"`

All Stripe calls mockable in tests.

**Files:** `backend/app/integrations/stripe_client.py`, `backend/app/services/billing.py`, `backend/app/schemas/billing.py` (`BillingStatus`, `CheckoutSessionRequest`, `CheckoutSessionResponse`, `PortalSessionResponse`), `backend/tests/unit/test_billing_service.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_billing_service.py -q` — green.

---

## W4.3 — Billing API routes

**What:** `billing.py` router under `/{workspace_id}/billing`; thin handlers delegate to `billing.py` service; `STRIPE_ENABLED` guard on POST routes; commit after success; audit on checkout/portal session creation.

**Files:** `backend/app/api/v1/workspaces/billing.py`, `backend/app/api/v1/workspaces/__init__.py`, `backend/tests/unit/test_billing_routes.py` (service mocks — no `tests/api/`)

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_billing_routes.py tests/unit/test_billing_service.py -q` — green.

---

## W4.4 — Stripe webhook handler

**What:** `webhooks/stripe.py` — `handle_stripe_webhook(payload: bytes, signature: str)`; verify signature; insert `event_id` (skip if exists); dispatch by `event.type`; update workspace; `record_audit` on subscription changes. Mount router on `api_v1_router` **without** `get_current_user` dependency.

**Files:** `backend/app/api/v1/webhooks/stripe.py`, `backend/app/api/v1/webhooks/__init__.py`, `backend/app/api/v1/__init__.py`, `backend/tests/unit/test_stripe_webhook.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_stripe_webhook.py -q` — green.

---

## W4.5 — `require_plan_feature` + installations gate

**What:** `plan_gates.py` — `PLAN_FEATURES`, `require_plan_feature("installations.create")` FastAPI dependency loading workspace plan from DB. Apply to `post_workspace_installation` in `workspaces/installations.py`. Extend `useExtensions` / widget filter to respect `minPlan` when W4 ships (optional: `plan-summary` always visible to admin).

**Files:** `backend/app/core/plan_gates.py`, `backend/app/api/v1/workspaces/installations.py`, `frontend/src/platform/extensions/hooks.ts` (optional `minPlan` filter), `backend/tests/unit/test_plan_gates.py`

**Deliverable:** `cd backend && pipenv run pytest tests/unit/test_plan_gates.py -q` — green (free → forbidden, pro → allowed).

---

## W4.6 — Billing settings UI + plan dashboard widget

**What:**

| Surface | Behavior |
|---------|----------|
| **`/settings/billing`** | Current plan badge; Upgrade → `POST checkout-session` redirect; Manage → `POST portal-session` redirect; disabled state when `!stripe_enabled` |
| **Sidebar** | Enable `settings.nav.billing` link |
| **Checklist** | `setup_billing`: `available: true`, `isComplete: plan === 'pro'`, `href: /settings/billing` |
| **`PlanSummaryWidget`** | Register `plan-summary` in `registerRevy.ts` or `registerBillingExtensions()`; show plan + link to billing |

**Router:**

```text
settings/billing → RequirePermission admin:users → BillingSettingsPage
```

**Files:** `frontend/src/features/settings/pages/BillingSettingsPage.tsx`, `frontend/src/features/settings/api.ts` + `hooks.ts`, `frontend/src/features/dashboard/widgets/PlanSummaryWidget.tsx`, `frontend/src/features/dashboard/checklistSteps.ts`, `frontend/src/features/settings/layout/SettingsSidebar.tsx`, `frontend/src/lib/routerInstance.tsx`, `frontend/.env.example`, i18n `settings.billing.*`, `dashboard.planSummary.*`, `errors.plan_upgrade_required`, `errors.billing_disabled` EN+LV, tests

**Deliverable:** `cd frontend && npm run lint && npm test -- --run BillingSettingsPage PlanSummaryWidget checklistSteps settings && npm run build` — green.

---

**Phase gate** (from `backend/`):

```bash
pipenv run lint && pipenv run pytest tests/unit/test_billing_config.py tests/unit/test_billing_service.py tests/unit/test_billing_routes.py tests/unit/test_stripe_webhook.py tests/unit/test_plan_gates.py -q
```

**Phase gate** (from `frontend/`):

```bash
npm run lint && npm test -- --run BillingSettingsPage PlanSummaryWidget checklistSteps settings && npm run build
```

**Human gate:** Stripe test-mode Checkout + `stripe listen --forward-to localhost:8000/api/v1/webhooks/stripe` verified once on staging — see [STRIPE_BILLING_SETUP.md](../../utils/STRIPE_BILLING_SETUP.md); unit gates suffice for commit; operator confirms before prod keys.

**Deploy:** `alembic upgrade head`; set Stripe env vars per [STRIPE_BILLING_SETUP.md](../../utils/STRIPE_BILLING_SETUP.md); configure webhook URL in Stripe Dashboard → `https://<api>/api/v1/webhooks/stripe`.

**Next:** [SAAS_BASE_W5_EXECUTION.md](./SAAS_BASE_W5_EXECUTION.md)
