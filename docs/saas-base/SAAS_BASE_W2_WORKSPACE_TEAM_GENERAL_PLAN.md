# SaaS base W2 — workspace & team

General plan from [SAAS_BASE_FINDINGS.md](./SAAS_BASE_FINDINGS.md). **No execution steps.**

**Cross-cutting:** unit tests; EN+LV; `admin:users` on mutating routes; audit writes for team/workspace mutations.

**API split:** team/workspace **APIs** in **W0**; **UI + audit** in **W2** (see findings §B).

---

## Goal

Workspace **admin** manages tenant settings, team, integrations entry, permissions reference — plus **audit table** (locked schema).

**Scope:** In — `/settings/workspace` (rename via W0 PATCH; slug read-only); `/settings/team` (members, invites, matrix; read-only for non-admins); `/settings/integrations` (extension slot + Revy card → `/installations`); `api_audit` migration; `record_audit()` on workspace/team/invitation mutations; `RequirePermission` on workspace admin routes. Out — billing (W4), danger zone (W6), workspace **suspend** (W5), audit **read** API (W3), dashboard registry finalize (W3).

**Deliverables:** Full team lifecycle UI; integrations tab live; audit rows on mutations; workspace-scoped settings nav.

**Depends on:** W0, W1.

**Status:** Done (shipped).

**Next:** [waves/SAAS_BASE_W2_EXECUTION.md](./waves/SAAS_BASE_W2_EXECUTION.md) → `phase-execution`.
