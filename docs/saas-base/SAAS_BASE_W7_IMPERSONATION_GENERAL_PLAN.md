# SaaS base W7 — impersonation

General plan from [SAAS_BASE_FINDINGS.md](./SAAS_BASE_FINDINGS.md). **No execution steps.**

**Cross-cutting:** unit tests; EN+LV; audit mandatory; ADR in execution file.

---

## Goal

**Support impersonation** for `super_admin` debugging — without Keycloak credential theft.

**Design (locked):**

- Real JWT remains bootstrap `super_admin` `sub` (Keycloak unchanged).
- `impersonation_sessions` in PostgreSQL; `CurrentUser.effective_user_id` for tenant RBAC.
- Mandatory **reason** on start; SPA banner; audit `impersonator_user_id` on all writes.
- Deny admin + destructive + billing mutation APIs while impersonating.

**Scope:** In — start/stop/active APIs; admin workspace members list for target picker; auth integration; banner; workspace detail impersonate action; audit UI impersonator column. Out — KC token exchange; auto-expire TTL v1; user notification.

**Depends on:** W2, W5, W6.

**Status:** Done (shipped).

**Next:** [waves/SAAS_BASE_W7_EXECUTION.md](./waves/SAAS_BASE_W7_EXECUTION.md) → `phase-execution`.
