# Review engineering context — execution index

**Program:** [../README.md](../README.md) · **Baseline:** [REVIEW_ENGINEERING_CONTEXT_FINDINGS.md](../REVIEW_ENGINEERING_CONTEXT_FINDINGS.md) · **General plan:** [REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md](../REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md)

**Authority:** [REVIEW_QUALITY_REVIEW_CONTEXT.md](../../review-quality/REVIEW_QUALITY_REVIEW_CONTEXT.md) (RC0; RC1/RC2/RC5 superseded by RCX) · RCX-D1–D12

**Goal:** Moonshot inject from SSOT manifest on scoped program PRs; Greptile via generated `files.json`; judge lock reuse; staging metrics prove inject + cap.

**Branch:** `feat/review-engineering-context` from `main`

## How we work (locked)

```text
P0 → P1 → P2 → P3 → P4 → P5
each phase: implement → pytest gate → Bugbot → commit (operator pushes; P5 human gate)
```

**Operator LOOP:** `phase-execution` skill — one commit per phase after gate + Bugbot. **LOOP pauses after P0.1** (Alembic `0029`). Fill [REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md](../REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md) in P5 (human gate).

## Decisions locked for execution

- **RCX-D11:** SSOT `.greptile/review-context.json`; Greptile `.greptile/files.json` **generated** in P3 (not hand-edited).
- **RCX-D10:** `revy_diff_max_bytes` default **524288** (512 KB) in P0 config; code uses config in P2.
- **RCX-D12:** Always inject lock/smoke extract; dedupe full MD body only when path in diff ∧ not omitted.
- **RCX-D8:** Inject block **before** unified diff; review instruction treats engineering block as authoritative.
- **SC coexistence:** `engineering_context_*` keys on same retrieve manifest as SC3 fields — no second manifest.
- **Module owner:** `app/services/engineering_context/` — parser (P0), loader+extract (P1), consumed by Moonshot (P2) and judge (P4).
- **P5 sign-off:** Requires P2–P4 on staging + deliberate dogfood PR (`--since` window non-empty).
- **P0 does not touch `.greptile/files.json`** — Greptile generator is P3; P0 adds SSOT path-exists validation (`engineering_context/validate.py`).

## LOOP order

| Phase | Focus | Execution | Status |
|-------|--------|-----------|--------|
| P0 — Foundations | Migration `0029`, SSOT, caps (settings only), path-exists CI | [REVIEW_ENGINEERING_CONTEXT_P0_EXECUTION.md](./REVIEW_ENGINEERING_CONTEXT_P0_EXECUTION.md) | done |
| P1 — Loader + extract | `fetch_repository_file_at_sha`, lock/smoke parser | [REVIEW_ENGINEERING_CONTEXT_P1_EXECUTION.md](./REVIEW_ENGINEERING_CONTEXT_P1_EXECUTION.md) | pending |
| P2 — Moonshot inject | `prepare_review_context`, populate metrics | [REVIEW_ENGINEERING_CONTEXT_P2_EXECUTION.md](./REVIEW_ENGINEERING_CONTEXT_P2_EXECUTION.md) | pending |
| P3 — Greptile sync | SSOT trim + generate `files.json` | [REVIEW_ENGINEERING_CONTEXT_P3_EXECUTION.md](./REVIEW_ENGINEERING_CONTEXT_P3_EXECUTION.md) | pending |
| P4 — Judge reuse | Lock block in judge prompt | [REVIEW_ENGINEERING_CONTEXT_P4_EXECUTION.md](./REVIEW_ENGINEERING_CONTEXT_P4_EXECUTION.md) | pending |
| P5 — Validation + closeout | Staging metrics, doc sync | [REVIEW_ENGINEERING_CONTEXT_P5_EXECUTION.md](./REVIEW_ENGINEERING_CONTEXT_P5_EXECUTION.md) | pending |

**Baseline (pre-RCX):** 25% diff truncated, 9/40 runs omitted `.md`, prompt p95 164k — see findings § Validation metrics.
