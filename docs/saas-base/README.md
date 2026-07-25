# SaaS base program (Revy repo)

**Fast-start foundation** for B2B multi-tenant apps on starter-pack rails — settings, dashboard, workspace admin, Stripe, platform ops, lifecycle, impersonation. Revy is first consumer; product code (`installations`, reviewer) stays **additive**.

**Prerequisite:** scaffold P0–P5 complete ([`docs/starter-pack/`](../starter-pack/)).

**Program status:** W0–W8 **complete** — see [waves/README.md](./waves/README.md).

**IA:** [SETTINGS_IA.md](./SETTINGS_IA.md) (committed; mirror in `internal-docs/starter-pack/` after W0).

---

## Planning

| Doc | Purpose |
|-----|---------|
| [SAAS_BASE_FINDINGS.md](./SAAS_BASE_FINDINGS.md) | Baseline, catalog, locked decisions |
| [SETTINGS_IA.md](./SETTINGS_IA.md) | Routes, sidebar groups, extension registry |
| `SAAS_BASE_W*_GENERAL_PLAN.md` | Per-wave goals (this folder) |
| [waves/README.md](./waves/README.md) | **Execution table** + LOOP status |

**Folder layout:** findings + general plans here; **execution** under `waves/` (~8 files) so this folder does not grow to ~20 files.

## Waves (general plans)

| Wave | General plan | Focus |
|------|--------------|--------|
| W0 | [W0 shell](./SAAS_BASE_W0_SHELL_GENERAL_PLAN.md) | Settings shell, header, team APIs |
| W1 | [W1 personal](./SAAS_BASE_W1_PERSONAL_SETTINGS_GENERAL_PLAN.md) | Profile, security, appearance |
| W2 | [W2 workspace](./SAAS_BASE_W2_WORKSPACE_TEAM_GENERAL_PLAN.md) | Team, integrations, audit schema |
| W3 | [W3 dashboard](./SAAS_BASE_W3_DASHBOARD_GENERAL_PLAN.md) | Registry, checklist, audit-lite |
| W4 | [W4 Stripe](./SAAS_BASE_W4_STRIPE_GENERAL_PLAN.md) | Stripe billing |
| W5 | [W5 platform](./SAAS_BASE_W5_PLATFORM_GENERAL_PLAN.md) | Platform admin (W5.1 / W5.2 at execution) |
| W6 | [W6 lifecycle](./SAAS_BASE_W6_LIFECYCLE_GENERAL_PLAN.md) | Danger zone, export/delete |
| W7 | [W7 impersonation](./SAAS_BASE_W7_IMPERSONATION_GENERAL_PLAN.md) | Impersonation |
| W8 | [W8 hardening](./SAAS_BASE_W8_PLATFORM_HARDENING_GENERAL_PLAN.md) | Ship readiness, doc sync, gap closure |

## Execution

| Wave | Execution | Status |
|------|-----------|--------|
| W0 | [waves/SAAS_BASE_W0_EXECUTION.md](./waves/SAAS_BASE_W0_EXECUTION.md) | done |
| W1 | [waves/SAAS_BASE_W1_EXECUTION.md](./waves/SAAS_BASE_W1_EXECUTION.md) | done |
| W2 | [waves/SAAS_BASE_W2_EXECUTION.md](./waves/SAAS_BASE_W2_EXECUTION.md) | done |
| W3 | [waves/SAAS_BASE_W3_EXECUTION.md](./waves/SAAS_BASE_W3_EXECUTION.md) | done |
| W4 | [waves/SAAS_BASE_W4_EXECUTION.md](./waves/SAAS_BASE_W4_EXECUTION.md) | done |
| W5 | [waves/SAAS_BASE_W5_EXECUTION.md](./waves/SAAS_BASE_W5_EXECUTION.md) | done |
| W6 | [waves/SAAS_BASE_W6_EXECUTION.md](./waves/SAAS_BASE_W6_EXECUTION.md) | done |
| W7 | [waves/SAAS_BASE_W7_EXECUTION.md](./waves/SAAS_BASE_W7_EXECUTION.md) | done |
| W8 | [waves/SAAS_BASE_W8_EXECUTION.md](./waves/SAAS_BASE_W8_EXECUTION.md) | done (`2145b41`) |

Full table: [waves/README.md](./waves/README.md).

## Locked principles

| Topic | Decision |
|-------|----------|
| **super_admin** | PG seed (`platform_role`) + KC user same email → first login activates ([BOOTSTRAP_SUPER_ADMIN.md](../../internal-docs/starter-pack/docs/backend/BOOTSTRAP_SUPER_ADMIN.md)); KC = credentials only |
| **Settings nav** | Two sidebar groups; **link only shipped waves** (no stub pages) |
| **Theme** | `localStorage` `app-theme` + `html.dark` per THEME.md; optional Zustand store — no DB column |
| **Extensions** | Single registry, multiple slots (dashboard, integrations, charts) |
| **Workspace RBAC** | Fixed 3 roles + read-only matrix |
| **Billing** | Workspace = Stripe Customer — setup: [STRIPE_BILLING_SETUP.md](../utils/STRIPE_BILLING_SETUP.md) |
| **Impersonation** | App-layer sessions; KC JWT unchanged; mandatory reason; audit `impersonator_user_id` |

---

## Cross-cutting (every wave)

Unit tests; EN+LV; hand-written Alembic; API RBAC + tenancy; starter-pack template sync; execution **peer-review** before `phase-execution`.

---

## Out of scope (this program)

Revy review pipeline; KC realm automation; KC Organizations; per-seat/usage/enterprise billing splits; deferred items above.

---

## Next

SaaS base W0–W8 **complete** (tag `saas-base-v1`). Maintenance: [OPS.md](./OPS.md), [STAGING_VERIFICATION.md](./STAGING_VERIFICATION.md), [Stripe billing setup](../utils/STRIPE_BILLING_SETUP.md).

**Active product program:** [Review pipeline (R0–R7)](../review-pipeline/README.md).
