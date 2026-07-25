# SaaS base W3 — dashboard

General plan from [SAAS_BASE_FINDINGS.md](./SAAS_BASE_FINDINGS.md). **No execution steps.**

**Cross-cutting:** unit tests; EN+LV; single [extension registry](./SETTINGS_IA.md#extension-registry-single-module).

---

## Goal

**Workspace-aware home** with wave-aware setup checklist, quick actions, and registered widgets.

**Scope:** In — finalize `platform/extensions` (`dashboard_widget` slot; W2 started `settings_integration`); welcome + workspace context; **setup checklist** with `available` flag (never show failed future steps); quick actions; `GET .../audit` read API + audit-lite card; Revy installations widget via registry. Out — plan summary card (W4), full activity page, platform KPIs (W5).

**Checklist rule:** Steps for W4+ billing use `available: false` until that wave ships — hidden, not red/X.

**Deliverables:** Dashboard grid layout; checklist truthful per shipped waves; activity card; one product widget; extension error boundaries.

**Depends on:** W0, W1, W2 (audit table + mutation rows).

**Status:** Done (shipped).

**Next:** [waves/SAAS_BASE_W3_EXECUTION.md](./waves/SAAS_BASE_W3_EXECUTION.md) → `phase-execution`.
