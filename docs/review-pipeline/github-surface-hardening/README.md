# GitHub surface hardening (post P0–P4)

**Status:** Execution plan peer-reviewed — ready for `phase-execution`. **Branch:** `feat/github-surface-hardening` (local only).

**Prerequisite:** [post-review-quality](../post-review-quality/README.md) P0–P4 merged ([#52](https://github.com/raimondskrauklis/revy/pull/52)).

**Thesis:** Close the **lifecycle** gap between Revy and Greptile on GitHub — thread resolve, GraphQL scale, publish testability — without opening track B (recall/STRUCT).

---

## Execution (LOOP order)

| Phase | Focus | Execution | Status |
|-------|--------|-----------|--------|
| P0 — Foundations | Thread map v2 + Greptile/Bugbot | [GITHUB_SURFACE_HARDENING_P0_EXECUTION.md](./GITHUB_SURFACE_HARDENING_P0_EXECUTION.md) | pending |
| P1 — Auto-resolve | GH-1, GH-1b (Option A) | [GITHUB_SURFACE_HARDENING_P1_EXECUTION.md](./GITHUB_SURFACE_HARDENING_P1_EXECUTION.md) | pending |
| P2 — GraphQL scale | GH-2, GH-3 | [GITHUB_SURFACE_HARDENING_P2_EXECUTION.md](./GITHUB_SURFACE_HARDENING_P2_EXECUTION.md) | pending |
| P3 — Edge cases | GH-4, GH-5 | [GITHUB_SURFACE_HARDENING_P3_EXECUTION.md](./GITHUB_SURFACE_HARDENING_P3_EXECUTION.md) | pending |
| P4 — Harness + sign-off | GH-6, GH-7 | [GITHUB_SURFACE_HARDENING_P4_EXECUTION.md](./GITHUB_SURFACE_HARDENING_P4_EXECUTION.md) | pending |

Index: [GITHUB_SURFACE_HARDENING_EXECUTION.md](./GITHUB_SURFACE_HARDENING_EXECUTION.md) · Dogfood: [GITHUB_SURFACE_HARDENING_DOGFOOD.md](./GITHUB_SURFACE_HARDENING_DOGFOOD.md)

---

## Docs (order)

| Step | Doc | Purpose |
|------|-----|---------|
| 1 | [GITHUB_SURFACE_HARDENING_FINDINGS.md](./GITHUB_SURFACE_HARDENING_FINDINGS.md) | Baseline |
| 2 | [GITHUB_SURFACE_HARDENING_GENERAL_PLAN.md](./GITHUB_SURFACE_HARDENING_GENERAL_PLAN.md) | Phases P0–P4 |
| 3 | [GITHUB_SURFACE_HARDENING_EXECUTION.md](./GITHUB_SURFACE_HARDENING_EXECUTION.md) | LOOP index |

---

## How we work

```text
findings → general plan → execution → phase-execution LOOP → one PR (docs + code per phase)
```

Greptile benchmark on real PR pushes. Revybot triaged before Greptile maintainability noise.
