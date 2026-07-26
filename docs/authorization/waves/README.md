# User provisioning — execution index

Linear **phase-execution** order. General plan: [`../USER_PROVISIONING_GENERAL_PLAN.md`](../USER_PROVISIONING_GENERAL_PLAN.md).

**Authority:** [`../USER_PROVISIONING_FINDINGS.md`](../USER_PROVISIONING_FINDINGS.md), `internal-docs/starter-pack/docs/backend/USER_REGISTRATION.md`, `AUTHZ_MODEL.md`, `BOOTSTRAP_SUPER_ADMIN.md`.

| Phase | File | Status |
|-------|------|--------|
| P0 — Unified provision service | [USER_PROVISIONING_P0_EXECUTION.md](./USER_PROVISIONING_P0_EXECUTION.md) | pending |
| P1 — Keycloak webhook API | [USER_PROVISIONING_P1_EXECUTION.md](./USER_PROVISIONING_P1_EXECUTION.md) | pending |
| P3 — Bootstrap & email hardening | [USER_PROVISIONING_P3_EXECUTION.md](./USER_PROVISIONING_P3_EXECUTION.md) | pending |
| P2 — Keycloak event listener (deploy) | [USER_PROVISIONING_P2_EXECUTION.md](./USER_PROVISIONING_P2_EXECUTION.md) | pending |
| P4 — Docs & operator smoke | [USER_PROVISIONING_P4_EXECUTION.md](./USER_PROVISIONING_P4_EXECUTION.md) | pending |

**LOOP order note:** P0 → P1 → P3 → P2 → P4. P3 before P2 so bootstrap guard ships before KC deploy; P2 human gate before P4 tier-B smoke.

**Pre-flight:** General plan § Program invariants (D8–D12) — devil's advocate pass 2026-07-26.
