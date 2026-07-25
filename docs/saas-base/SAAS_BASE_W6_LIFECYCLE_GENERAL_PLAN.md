# SaaS base W6 — lifecycle & compliance

General plan from [SAAS_BASE_FINDINGS.md](./SAAS_BASE_FINDINGS.md). **No execution steps.**

**Cross-cutting:** unit tests; EN+LV; audit append-only; destructive actions require confirmation UX.

**Authority:** `internal-docs/starter-pack/docs/backend/ACCOUNT_LIFECYCLE.md`, `AUDIT.md`.

---

## Goal

**Account and workspace lifecycle**: export, delete, leave — danger zone only.

**Scope:** In — `/settings/danger`; async export jobs + download; `UserStatus.deleted` / `WorkspaceStatus.deleted`; leave/delete guards (last admin, sole admin, active subscription); lifecycle audit events; typed confirmation modals. Out — notification prefs (**deferred**), Keycloak user deletion, legal hold UI.

**Deliverables:** Export, delete, leave flows testable end-to-end; audit covers lifecycle mutations.

**Depends on:** W1, W2, W4.

**Status:** Done (shipped).

**Next:** [waves/SAAS_BASE_W6_EXECUTION.md](./waves/SAAS_BASE_W6_EXECUTION.md) → `phase-execution`.
