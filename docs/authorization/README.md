# Authorization & identity

Findings and plans for **Keycloak → Revy user provisioning**, registration modes, and platform bootstrap.

| Doc | Purpose |
|-----|---------|
| [USER_PROVISIONING_FINDINGS.md](./USER_PROVISIONING_FINDINGS.md) | Baseline — actual code vs docs, gaps |
| [USER_PROVISIONING_GENERAL_PLAN.md](./USER_PROVISIONING_GENERAL_PLAN.md) | Phased plan — P0–P4 (locked decisions) |
| [waves/README.md](./waves/README.md) | Execution index — phase-execution LOOP order |

**Program status:** shipped (2026-07-26) — webhook primary + JIT fallback via `provision_user_from_keycloak()`.

**Architecture:**

```mermaid
flowchart LR
  KC[Keycloak identity events] -->|POST internal webhook| WH[/api/v1/webhooks/keycloak]
  WH --> PG[(PostgreSQL users)]
  SPA[SPA login + JWT] -->|GET /api/v1/me JIT fallback| PG
```

**Authority (starter-pack):** `internal-docs/starter-pack/docs/backend/AUTHZ_MODEL.md`, `USER_REGISTRATION.md`, `BOOTSTRAP_SUPER_ADMIN.md`, `TENANCY.md`

**Revy runbooks:** [docs/starter-pack/REGISTRATION_FLAGS.md](../starter-pack/REGISTRATION_FLAGS.md), [KEYCLOAK_DEV_CHECKLIST.md](../starter-pack/KEYCLOAK_DEV_CHECKLIST.md), [DEV_BOOTSTRAP.md](../starter-pack/DEV_BOOTSTRAP.md)
