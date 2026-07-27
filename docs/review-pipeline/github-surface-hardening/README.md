# GitHub surface hardening (post P0–P4)

**Status:** Findings baseline — general plan next.

**Prerequisite:** [post-review-quality](../post-review-quality/README.md) P0–P4 merged ([#52](https://github.com/raimondskrauklis/revy/pull/52)).

**Thesis:** Close the **lifecycle** gap between Revy and Greptile on GitHub — thread resolve, GraphQL scale, publish testability — without opening track B (recall/STRUCT).

---

## Docs (order)

| Step | Doc | Purpose |
|------|-----|---------|
| 1 | [GITHUB_SURFACE_HARDENING_FINDINGS.md](./GITHUB_SURFACE_HARDENING_FINDINGS.md) | Baseline — **start here** |
| 2 | `GITHUB_SURFACE_HARDENING_GENERAL_PLAN.md` | Phases (after findings peer-review) |
| 3 | `GITHUB_SURFACE_HARDENING_EXECUTION.md` | Execution index (after general plan) |

**Prior program:** [post-review-quality/POST_REVIEW_QUALITY_FOLLOWUPS.md](../post-review-quality/POST_REVIEW_QUALITY_FOLLOWUPS.md) (seed → absorbed into findings).

---

## How we work

```text
findings → general plan → execution LOOP → dogfood row → merge
```

Greptile remains benchmark on real PR pushes. Revybot findings triaged **before** Greptile maintainability noise.
