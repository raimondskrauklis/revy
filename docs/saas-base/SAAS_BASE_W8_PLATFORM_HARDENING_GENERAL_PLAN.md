# SaaS base W8 — Platform hardening & ship readiness

General plan from [SAAS_BASE_FINDINGS.md](./SAAS_BASE_FINDINGS.md). **No execution steps.**

**Depends on W0–W7 shipped.** **Not a feature wave** — closes gaps from post-W7 platform review (permission leaks, data accuracy, impersonation holes, ops runbooks, stale program docs).

**Authority:** W0–W7 execution files, [SETTINGS_IA.md](./SETTINGS_IA.md), `docs/starter-pack/`, `docs/utils/`, `deploy/env-examples/`, root `AGENTS.md`.

---

## Goal

Make SaaS base **production-honest**: no admin-only API calls for viewers, nav matches RBAC, impersonation deny-list complete, KPIs and checklist accurate, export/Stripe ops documented, human gates captured in a staging checklist, and **all platform docs + runbooks in sync** with shipped code.

**Deliverables:** W8 phase gate green; staging verification checklist committed; findings baseline reflects shipped W0–W8; no duplicate execution doc trees.

**Status:** Done (shipped).

**Next:** [waves/SAAS_BASE_W8_EXECUTION.md](./waves/SAAS_BASE_W8_EXECUTION.md) → `phase-execution`.

---

## Scope (in)

| Area | Gap closed |
|------|------------|
| **Tenant UX** | Read-only `workspace_plan` on `/me`; no billing API for plan display; permission-aware settings sidebar; suspended-workspace status page; filter suspended/deleted from switcher |
| **Impersonation** | Deny `POST .../leave` while impersonating; `impersonator_user_id` on all lifecycle audits |
| **i18n** | EN+LV for `workspace_suspended`, all `impersonation_*` error codes |
| **Data accuracy** | Admin KPIs exclude `deleted` workspaces; invitation list excludes expired; accurate member count for checklist |
| **Billing ops** | Documented orphan-webhook policy (align code with findings); plan semantics (`past_due` → pro) in [STRIPE_BILLING_SETUP.md](../utils/STRIPE_BILLING_SETUP.md) |
| **Deploy** | `EXPORT_*` in deploy examples; Celery `maintenance` queue documented; export + Stripe staging steps |
| **Docs** | Findings, general plans, READMEs, SETTINGS_IA, AGENTS.md, DEV_BOOTSTRAP, runbooks, fast-start strip list; remove `waves/w0`…`w7` duplicates |

## Out of scope (remain deferred)

Notifications, API keys, file uploads, in-app user directory, impersonation TTL cron, per-seat/usage billing, changelog UI (file may stay; wire only if trivial).

---

## Subphase map (execution)

| Id | Focus |
|----|--------|
| W8.1 | Tenant UX + read-only plan on `/me` |
| W8.2 | Impersonation closure + error i18n |
| W8.3 | Data accuracy (KPIs, invitations, member count) |
| W8.4 | Billing webhook policy + plan semantics |
| W8.5 | Ops deploy parity + staging verification checklist |
| W8.6 | Platform-wide doc sync (runbooks, findings, dedupe) |

---

## Success criteria

- Viewer/operator dashboard loads without billing 403.
- Settings sidebar shows only routes the user can access.
- Impersonator cannot leave workspace; audit shows impersonator on lifecycle writes.
- Admin KPI `workspaces_total` consistent with active + suspended (+ deleted if reported separately).
- Expired invitations not listed as pending.
- Checklist member count correct beyond 50 members.
- `docs/saas-base/SAAS_BASE_FINDINGS.md` describes shipped state (not stubs).
- Single execution doc tree under `docs/saas-base/waves/*.md`.
