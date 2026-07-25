# SaaS base W4 — Stripe billing

General plan from [SAAS_BASE_FINDINGS.md](./SAAS_BASE_FINDINGS.md). **No execution steps.**

**Isolated wave** — billing is complex enough to own full attention; do not mix with settings or dashboard work.

**Cross-cutting:** unit tests; idempotent webhook handling; secrets in env only; EN+LV for billing UI strings.

**Authority:** `internal-docs/starter-pack/docs/backend/BILLING.md`, [Stripe SaaS guide](https://docs.stripe.com/saas), committed runbook [STRIPE_BILLING_SETUP.md](../utils/STRIPE_BILLING_SETUP.md).

---

## Goal

**Full Stripe integration** with workspace as billing unit: self-serve upgrade, portal management, webhook-synced plan state, API enforcement.

**Scope:** In — `billing` service + Stripe client; env config (`STRIPE_ENABLED`, keys, price ID); Checkout + Portal session APIs; webhook with signature + idempotency; sync `workspaces.plan` + `stripe_customer_id`; `require_plan_feature()` on at least one Revy route; `/settings/billing`; plan-summary dashboard widget; checklist billing step. Out — metering, custom card UI, `plan_limit()` quotas, enterprise splits, dunning automation.

**Deliverables:** Test-mode flow: free → Checkout → webhook → `plan=pro` → gated endpoint allowed; `STRIPE_ENABLED=false` dev mode works without Stripe.

**Depends on:** W0, W2, W3.

**Status:** Shipped (W4). Hardening: W8 webhook orphan policy + runbook sync.

**Next:** [waves/SAAS_BASE_W8_EXECUTION.md](./waves/SAAS_BASE_W8_EXECUTION.md) (W8.4 billing ops).
