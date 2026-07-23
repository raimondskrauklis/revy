# Starter-pack scaffold (Revy repo)

Planning docs for greenfield scaffold from `internal-docs/starter-pack/` into this repo.

## Planning

| Doc | Purpose |
|-----|---------|
| [SCAFFOLD_FINDINGS.md](./SCAFFOLD_FINDINGS.md) | Baseline — what exists, gaps, locked decisions |
| [SCAFFOLD_GENERAL_PLAN.md](./SCAFFOLD_GENERAL_PLAN.md) | Phased goals (no execution steps) |

Execution plans peer-reviewed (final pass 2026-07-24) — see findings § Peer review. **Unblocked for `phase-execution` from P1.**

## Execution (phase-execution LOOP order)

| Phase | File | Status |
|-------|------|--------|
| P0 — Scaffold baseline | [SCAFFOLD_P0_EXECUTION.md](./SCAFFOLD_P0_EXECUTION.md) | Done (2026-07-23) |
| P1 — Runnable dev platform | [SCAFFOLD_P1_EXECUTION.md](./SCAFFOLD_P1_EXECUTION.md) | Done (2026-07-24) — human Keycloak smoke pending |
| P2 — Registration & platform flows | [SCAFFOLD_P2_EXECUTION.md](./SCAFFOLD_P2_EXECUTION.md) | Done (2026-07-24) |
| P3 — Shared platform hardening | [SCAFFOLD_P3_EXECUTION.md](./SCAFFOLD_P3_EXECUTION.md) | Done (2026-07-24) |
| P4 — Revy product foundation | [SCAFFOLD_P4_EXECUTION.md](./SCAFFOLD_P4_EXECUTION.md) | pending |
| P5 — Repo identity & automation | [SCAFFOLD_P5_EXECUTION.md](./SCAFFOLD_P5_EXECUTION.md) | **deferred** |

**Authority:** `internal-docs/starter-pack/` + `internal-docs/product/revy/` (gitignored). Committed runbooks: `DEV_BOOTSTRAP.md`, `REGISTRATION_FLAGS.md`, `KEYCLOAK_DEV_CHECKLIST.md` (P1); `REVY_PRODUCT_SLICE.md` (P4.1).

**Locked exclusions (Phases 1–4):** `.cursorrules`, deploy workflow, root `AGENTS.md`/`README` — see [findings § Locked exclusions](./SCAFFOLD_FINDINGS.md#locked-exclusions).

**Next:** `phase-execution` → [SCAFFOLD_P4_EXECUTION.md](./SCAFFOLD_P4_EXECUTION.md)
