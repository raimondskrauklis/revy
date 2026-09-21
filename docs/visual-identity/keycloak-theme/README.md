# docs/visual-identity/keycloak-theme/README.md

# Keycloak login theme — execution index

| Phase | File | Status | SHA |
|:---|:---|:---|:---|
| P0 — Inspector (read-only) | [KEYCLOAK_THEME_P0_EXECUTION.md](./KEYCLOAK_THEME_P0_EXECUTION.md) | Done | `090b411` |
| P1 — Theme package + local loop | [KEYCLOAK_THEME_P1_EXECUTION.md](./KEYCLOAK_THEME_P1_EXECUTION.md) | Done | `090b411` |
| P2 — Transport, apply, realm cutover | [KEYCLOAK_THEME_P2_EXECUTION.md](./KEYCLOAK_THEME_P2_EXECUTION.md) | Done | (local) |
| P3 — Bake + docker-compose sync | [KEYCLOAK_THEME_P3_EXECUTION.md](./KEYCLOAK_THEME_P3_EXECUTION.md) | Done | (local) |

**LOOP order:** P0 → P1 → P2 → P3 (P3 optional, deferred).

**Scope authority:** [KEYCLOAK_THEME_FINDINGS.md](./KEYCLOAK_THEME_FINDINGS.md) Q1–Q13 locked · [KEYCLOAK_THEME_GENERAL_PLAN.md](./KEYCLOAK_THEME_GENERAL_PLAN.md) P0–P3.  
No backend/frontend code — `infra/**`, `.github/workflows/**` (optional CI), `docs/visual-identity/keycloak-theme/**`.  
**Not:** SPA React, JWT/RBAC, Alembic, admin/account/email themes. No pytest/Vitest — visual QA only.  

**Review:** [architecture peer review](./reviews/architecture-peer-review/README.md) — latest pass 2 (delta), BLOCK create-execution-plan: no. [Execution peer review](./reviews/execution-peer-review/README.md) — latest pass 2 (delta), BLOCK phase-execution: no.
