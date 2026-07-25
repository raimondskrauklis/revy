# Stripe billing setup (Revy)

How to configure Stripe for Revy on a **droplet** (staging/production). Revy uses **Stripe Checkout** (hosted redirect) and **Customer Portal** — no Stripe Elements on the frontend in v1.

**Verified against:** [Stripe API keys](https://docs.stripe.com/keys), [Webhooks](https://docs.stripe.com/webhooks), [Checkout fulfillment](https://docs.stripe.com/checkout/fulfillment), Revy W4 (`docs/saas-base/waves/SAAS_BASE_W4_EXECUTION.md`).

**Related:** `deploy/env-examples/backend.env.production.example`, `backend/.env.example`, `deploy/nginx/revy.createit.digital.conf`, [OPS.md](../saas-base/OPS.md), [STAGING_VERIFICATION.md](../saas-base/STAGING_VERIFICATION.md).

---

## How the flow works

```text
User (Settings → Billing)
  → POST /api/v1/workspaces/{id}/billing/checkout-session
  → API creates Stripe Checkout Session (subscription mode)
  → Browser redirects to checkout.stripe.com
  → User pays or cancels
  → Stripe redirects to success_url or cancel_url (SPA)
  → Stripe POSTs webhook to /api/v1/webhooks/stripe
  → API verifies signature, updates workspaces.plan (source of truth)
```

Important (from Stripe docs):

- **`success_url` / `cancel_url`** are for UX only — the user may close the browser before redirect.
- **`checkout.session.completed`** (and subscription lifecycle webhooks) are what actually sync the workspace plan in Revy.
- Webhook endpoints must be **public HTTPS URLs** ([Stripe webhooks](https://docs.stripe.com/webhooks)).

---

## Environment variables

Set on the droplet in `/mnt/revy_volume/backend/.env` (see `deploy/env-examples/backend.env.production.example`).

| Variable | Required when enabled | Purpose |
|----------|----------------------|---------|
| `STRIPE_ENABLED` | yes | `true` to enable Checkout, Portal, and webhook handler |
| `STRIPE_SECRET_KEY` | yes | Server-side API key (`sk_test_…` or `sk_live_…`) |
| `STRIPE_WEBHOOK_SECRET` | yes | Signing secret for your **Dashboard** webhook endpoint (`whsec_…`) |
| `STRIPE_PRICE_PRO` | yes | Recurring **Price ID** for Pro (`price_…`, not `prod_…`) |
| `APP_PUBLIC_URL` | yes | SPA origin — used for Portal return URL and Checkout URL fallbacks |
| `STRIPE_CHECKOUT_SUCCESS_URL` | optional | Override success redirect (default: `{APP_PUBLIC_URL}/settings/billing?checkout=success`) |
| `STRIPE_CHECKOUT_CANCEL_URL` | optional | Override cancel redirect (default: `{APP_PUBLIC_URL}/settings/billing?checkout=cancel`) |

Example (test mode on droplet):

```env
STRIPE_ENABLED=true
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_PRO=price_...
APP_PUBLIC_URL=https://revy.createit.digital
```

Optional frontend (`frontend/.env` / build secrets) — **not required** for Checkout redirect v1:

```env
# VITE_STRIPE_PUBLISHABLE_KEY=pk_test_...
```

When `STRIPE_ENABLED=false`, billing mutations return `billing_disabled`; `GET …/billing` returns `plan: free`, `stripe_enabled: false`.

---

## Where to find each value in Stripe

Use **Test mode** (toggle in the Stripe Dashboard) for droplet testing with `sk_test_` keys. Test mode works on public URLs; you do not need live keys until real payments.

### `STRIPE_SECRET_KEY`

**Dashboard → Developers → API keys**

- Test: https://dashboard.stripe.com/test/apikeys
- Live: https://dashboard.stripe.com/apikeys

Copy **Secret key** (Reveal). Prefix: `sk_test_` (test) or `sk_live_` (live).

Store only in server env — never in frontend or git.

### `STRIPE_PRICE_PRO`

**Dashboard → Product catalog → Products**

1. Create a product (e.g. “Pro”).
2. Add a **recurring** price (monthly or yearly).
3. Copy the **Price ID** (`price_…`).

Revy Checkout uses `mode=subscription` with this price ID. The Product ID (`prod_…`) is not what you put in env.

### `STRIPE_WEBHOOK_SECRET` (droplet — no Stripe CLI)

**Dashboard → Developers → Webhooks → Add endpoint**

1. **Endpoint URL:** `https://<your-host>/api/v1/webhooks/stripe`  
   For Revy droplet: `https://revy.createit.digital/api/v1/webhooks/stripe`
2. **Listen to:** your own account (not Connect).
3. **Events** (Revy handles these):
   - `checkout.session.completed`
   - `customer.subscription.updated`
   - `customer.subscription.deleted`
   - `invoice.paid`
   - `invoice.payment_failed`
4. After creating the endpoint, open it → **Reveal** signing secret → `whsec_…`

Put that value in `STRIPE_WEBHOOK_SECRET` on the droplet.

**Note:** If you use `stripe listen` locally, its `whsec_` is **different** from the Dashboard endpoint secret. For droplet testing, use the Dashboard secret only ([signature verification](https://docs.stripe.com/webhooks/signature)).

### Checkout redirect URLs

Not from Stripe — they are your SPA URLs. If `APP_PUBLIC_URL` is set, Revy builds them automatically:

- Success: `https://revy.createit.digital/settings/billing?checkout=success`
- Cancel: `https://revy.createit.digital/settings/billing?checkout=cancel`

Override with `STRIPE_CHECKOUT_SUCCESS_URL` / `STRIPE_CHECKOUT_CANCEL_URL` if needed.

---

## Droplet checklist

1. **Migration** — `stripe_webhook_events` table must exist:
   ```bash
   alembic upgrade head
   ```
2. **Backend env** — set Stripe variables in `/mnt/revy_volume/backend/.env`.
3. **Restart API** — reload containers/service after env changes.
4. **Stripe webhook** — create endpoint pointing at `https://<host>/api/v1/webhooks/stripe` (HTTPS required).
5. **Test** — open `https://<host>/settings/billing`, click Upgrade, pay with test card `4242 4242 4242 4242` ([Stripe testing](https://docs.stripe.com/testing)).
6. **Verify webhook** — Dashboard → Webhooks → your endpoint → **Recent deliveries** should show `200` responses.

---

## API surface (reference)

| Method | Path | Auth | Purpose |
|--------|------|------|---------|
| `GET` | `/api/v1/workspaces/{workspace_id}/billing` | JWT | Current plan + `stripe_enabled` |
| `POST` | `/api/v1/workspaces/{workspace_id}/billing/checkout-session` | JWT (admin) | Body: `{ "plan": "pro" }` → `{ "url": "…" }` |
| `POST` | `/api/v1/workspaces/{workspace_id}/billing/portal-session` | JWT (admin) | `{ "url": "…" }` (needs `stripe_customer_id`) |
| `POST` | `/api/v1/webhooks/stripe` | **None** (Stripe signature) | Webhook handler |

Billing unit is **workspace** (`workspaces.plan`, `workspaces.stripe_customer_id`). Plans v1: `free` | `pro`.

---

## Troubleshooting

| Symptom | Likely cause |
|---------|----------------|
| “Billing is not configured” in UI | `STRIPE_ENABLED=false` or missing keys on API |
| Checkout works but plan stays `free` | Webhook not configured, wrong `whsec_`, or non-200 from API |
| Webhook signature errors | `STRIPE_WEBHOOK_SECRET` from wrong source (CLI vs Dashboard) or test/live mismatch |
| Checkout error on upgrade | Wrong `STRIPE_PRICE_PRO` (product ID instead of price ID, or live price with test key) |
| Webhook 404 | Wrong URL path — must be `/api/v1/webhooks/stripe` |

Check nginx routes public API at `https://<host>/api/v1` (`deploy/nginx/revy.createit.digital.conf`).

---

## Webhook policy (W8)

| Event | No matching workspace | Handler behavior |
|-------|----------------------|------------------|
| `checkout.session.completed` | Missing `workspace_id` metadata or workspace row | **500** (`BillingWebhookError`) — Stripe retries |
| `customer.subscription.*` | Customer not linked to any workspace | **200** — log `stripe_subscription_orphan`, no DB change |
| `invoice.*` | Customer not linked | **200** — no-op |

**Plan semantics:** `past_due` subscriptions keep `pro` until Stripe sends `customer.subscription.deleted` or the price no longer matches `STRIPE_PRICE_PRO` (then `free`). Gated features: see `backend/app/services/plan_gates.py`.
