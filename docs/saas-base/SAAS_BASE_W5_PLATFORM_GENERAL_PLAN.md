# SaaS base W5 — platform admin

General plan from [SAAS_BASE_FINDINGS.md](./SAAS_BASE_FINDINGS.md). **No execution steps.**

**Cross-cutting:** unit tests; EN+LV; `super_admin` via `users.platform_role` (not Keycloak roles); audit platform mutations + detail views.

**Sizing:** execution splits workspace directory (W5.1–W5.2 checkpoint) then KPIs + audit + settings (W5.3–W5.6).

**Bootstrap:** super_admin = PostgreSQL seed + Keycloak login same email ([BOOTSTRAP_SUPER_ADMIN.md](../../internal-docs/starter-pack/docs/backend/BOOTSTRAP_SUPER_ADMIN.md)). KC manages credentials; PG grants `/admin/*` access.

---

## Goal

Platform operator surface: workspace oversight, KPIs, audit search, platform config — **no in-app user directory** (Keycloak Admin).

**Scope:** In — `AdminLayout` + `/admin/dashboard` KPIs; `/admin/workspaces` list/detail/suspend; `/admin/audit` search; `/admin/settings` (flags + KC link); migrate `/admin/users` under admin shell; suspended-workspace tenant guard. Out — in-app user CRUD (**deferred**); impersonation (**W7**).

**Auth:** `require_super_admin()` / `RequirePlatformAdmin` — not workspace `admin:users`.

**Deliverables:** super_admin can find/suspend workspaces; audit searchable cross-tenant; KPIs live; KC link for identity ops.

**Depends on:** W2 (audit table), W4 (plan on workspace detail).

**Status:** Done (shipped).

**Next:** [waves/SAAS_BASE_W5_EXECUTION.md](./waves/SAAS_BASE_W5_EXECUTION.md) → `phase-execution`.
