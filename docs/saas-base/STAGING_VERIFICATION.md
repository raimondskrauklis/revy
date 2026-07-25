# SaaS base — staging verification (human gate)

Run on **staging** before production SaaS base sign-off (W0–W8). Code may ship without this checklist; record pass/fail + operator + date in team notes.

**Prerequisites:** `alembic upgrade head` through `0009`; Keycloak realm; Celery worker on `maintenance,default`; Stripe test mode configured per [STRIPE_BILLING_SETUP.md](../utils/STRIPE_BILLING_SETUP.md).

---

## Auth & bootstrap

| # | Step | Pass |
|---|------|------|
| 1 | Open staging SPA → Keycloak login | ☐ |
| 2 | `GET /api/v1/me` → `status: active`, memberships | ☐ |
| 3 | Bootstrap super_admin (if fresh env): seed script + KC same email → first login | ☐ |
| 4 | Mode A registration: new user lands on dashboard without approval | ☐ |

---

## Settings & RBAC (W0–W2, W8)

| # | Step | Pass |
|---|------|------|
| 5 | **Viewer** member: settings sidebar hides Workspace, Billing, Danger | ☐ |
| 6 | **Admin** member: all workspace settings links visible | ☐ |
| 7 | Team invite → accept → member appears in list | ☐ |
| 8 | Expired pending invite not shown in team invitations list | ☐ |

---

## Dashboard & plan (W3, W8)

| # | Step | Pass |
|---|------|------|
| 9 | Viewer dashboard loads — **no** `403` on billing API (plan from `/me` `workspace_plan`) | ☐ |
| 10 | Setup checklist member step uses accurate count (not first-page only) | ☐ |
| 11 | Pro-gated extension hidden on free plan; visible after upgrade | ☐ |

---

## Stripe billing (W4)

See [STRIPE_BILLING_SETUP.md](../utils/STRIPE_BILLING_SETUP.md) for env vars, webhook URL, and test-mode flow.

| # | Step | Pass |
|---|------|------|
| 12 | Admin: Settings → Billing → Upgrade → Stripe Checkout (test card `4242…`) | ☐ |
| 13 | Webhook delivery `200`; workspace `plan` → `pro` | ☐ |
| 14 | Customer portal opens for admin | ☐ |
| 15 | Non-admin cannot open billing checkout | ☐ |

---

## Platform admin (W5)

| # | Step | Pass |
|---|------|------|
| 16 | Super_admin: `/admin/dashboard` KPIs load (`workspaces_total` excludes deleted) | ☐ |
| 17 | Workspace search + detail; audit log filters | ☐ |
| 18 | Signup queue (Mode B only) approve/reject | ☐ |

---

## Lifecycle & export (W6)

| # | Step | Pass |
|---|------|------|
| 19 | Danger zone: request data export → job completes → download ZIP | ☐ |
| 20 | Export file removed after TTL (spot-check path under `EXPORT_STORAGE_PATH`) | ☐ |
| 21 | Suspend workspace → member sees `/workspace-suspended` gate | ☐ |

---

## Impersonation (W7, W8)

| # | Step | Pass |
|---|------|------|
| 22 | Super_admin starts impersonation (reason ≥ 10 chars) → banner visible | ☐ |
| 23 | Effective user sees target's workspaces; mutations audit `impersonator_user_id` | ☐ |
| 24 | **Leave workspace** blocked while impersonating | ☐ |
| 25 | Stop impersonation → banner clears; audit `platform.impersonation.stopped` | ☐ |

---

## Sign-off

| Field | Value |
|-------|-------|
| Environment URL | |
| Operator | |
| Date | |
| Result | ☐ Pass / ☐ Fail (notes) |
