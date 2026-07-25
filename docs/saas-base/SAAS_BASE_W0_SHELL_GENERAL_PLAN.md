# SaaS base W0 — shell & workspace APIs

General plan from [SAAS_BASE_FINDINGS.md](./SAAS_BASE_FINDINGS.md). **No file lists or steps** — use `create-execution-plan` for W0.

**Cross-cutting:** unit tests; EN+LV; hand-written migrations; API enforcement before UI gates.

**IA:** [SETTINGS_IA.md](./SETTINGS_IA.md) — sidebar shows **only implemented** links (anti-facade).

---

## Goal

Establish **settings shell**, **app chrome**, and **workspace/team backend APIs** so later waves plug in without stub pages in nav.

**Scope:** In — nested `/settings` layout with Personal / Workspace sidebar **groups** (empty groups OK; no dead links); header workspace switcher + user menu; backend APIs: workspace general update, member list, role change, remove, invitation list, revoke (API RBAC server-side); `RequirePermission` on workspace settings **sub-routes** when linked (**W2**); committed [SETTINGS_IA.md](./SETTINGS_IA.md) + starter-pack mirror. Out — settings page content (W1+), billing, dashboard, platform admin UI, danger-zone actions.

**Deliverables:** Routable layout; switcher sets `X-Workspace-Id` via `PATCH /me/workspace`; workspace admin APIs + unit tests; **no sidebar links** to unimplemented settings sections.

**Depends on:** Completed scaffold (P0–P5).

**Status:** Done (shipped).

**Next:** [waves/SAAS_BASE_W0_EXECUTION.md](./waves/SAAS_BASE_W0_EXECUTION.md) → `phase-execution`.
