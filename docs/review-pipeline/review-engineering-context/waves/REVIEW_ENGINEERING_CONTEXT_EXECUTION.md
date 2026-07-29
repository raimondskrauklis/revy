# Review engineering context — execution index

**Program:** [../README.md](../README.md) · **Baseline:** [REVIEW_ENGINEERING_CONTEXT_FINDINGS.md](../REVIEW_ENGINEERING_CONTEXT_FINDINGS.md) · **General plan:** [REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md](../REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md)

**Authority:** [REVIEW_QUALITY_REVIEW_CONTEXT.md](../../review-quality/REVIEW_QUALITY_REVIEW_CONTEXT.md) (RC0; RC1/RC2/RC5 superseded by RCX) · RCX-D1–D17

**Goal:** Moonshot inject from SSOT manifest on scoped program PRs; Greptile via generated `files.json`; judge lock reuse; staging metrics prove inject + cap; Greptile-depth issue comment; operator API + gate tooling; sign-off.

**Branch:** `main` — P0–P4 shipped (#60). **P6–P8** = closeout wave (one real PR).

## How we work (locked)

```text
P0 → P1 → P2 → P3 → P4 → P5 (stub) → P6 → P7 → P8
each code phase: implement → pytest gate → Bugbot → commit (operator pushes)
P8: human gate only
```

**Operator LOOP:** `phase-execution` skill — one commit per phase after gate + Bugbot. P8 fills [REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md](../REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md).

## Decisions locked for execution

- **RCX-D11:** SSOT `.greptile/review-context.json`; Greptile `.greptile/files.json` **generated** in P3 (not hand-edited).
- **RCX-D10:** `revy_diff_max_bytes` default **524288** (512 KB) in P0 config; code uses config in P2.
- **RCX-D12:** Always inject lock/smoke extract; dedupe full MD body only when path in diff ∧ not omitted.
- **RCX-D8:** Inject block **before** unified diff; review instruction treats engineering block as authoritative.
- **RCX-D13–D17:** Wave 2 — issue comment depth; fallback parity; one PR P6+P7; no frontend; metrics script name retained.
- **SC coexistence:** `engineering_context_*` keys on same retrieve manifest as SC3 fields — no second manifest.
- **Module owner:** `app/services/engineering_context/` — parser (P0), loader+extract (P1), consumed by Moonshot (P2) and judge (P4).
- **P8 sign-off:** Requires P2–P4 on staging + P6 dogfood PR (`--since` window non-empty) + `--rcx-gate` PASS.

## LOOP order

| Phase | Focus | Execution | Status |
|-------|--------|-----------|--------|
| P0 — Foundations | Migration `0029`, SSOT, caps (settings only), path-exists pytest | [REVIEW_ENGINEERING_CONTEXT_P0_EXECUTION.md](./REVIEW_ENGINEERING_CONTEXT_P0_EXECUTION.md) | done |
| P1 — Loader + extract | `fetch_repository_file_at_sha`, lock/smoke parser | [REVIEW_ENGINEERING_CONTEXT_P1_EXECUTION.md](./REVIEW_ENGINEERING_CONTEXT_P1_EXECUTION.md) | done |
| P2 — Moonshot inject | `prepare_review_context`, populate metrics | [REVIEW_ENGINEERING_CONTEXT_P2_EXECUTION.md](./REVIEW_ENGINEERING_CONTEXT_P2_EXECUTION.md) | done |
| P3 — Greptile sync | SSOT trim + generate `files.json` | [REVIEW_ENGINEERING_CONTEXT_P3_EXECUTION.md](./REVIEW_ENGINEERING_CONTEXT_P3_EXECUTION.md) | done |
| P4 — Judge reuse | Lock block in judge prompt | [REVIEW_ENGINEERING_CONTEXT_P4_EXECUTION.md](./REVIEW_ENGINEERING_CONTEXT_P4_EXECUTION.md) | done |
| P5 — Validation stub | Memo stub; P5.5 moved to P6 | [REVIEW_ENGINEERING_CONTEXT_P5_EXECUTION.md](./REVIEW_ENGINEERING_CONTEXT_P5_EXECUTION.md) | stub done |
| P6 — Publish surface | Greptile-depth issue comment | [REVIEW_ENGINEERING_CONTEXT_P6_EXECUTION.md](./REVIEW_ENGINEERING_CONTEXT_P6_EXECUTION.md) | done |
| P7 — Operator visibility | `context_stats` API + `--rcx-gate` | [REVIEW_ENGINEERING_CONTEXT_P7_EXECUTION.md](./REVIEW_ENGINEERING_CONTEXT_P7_EXECUTION.md) | done |
| P8 — Closeout | Staging validation + doc sync + sign-off | [REVIEW_ENGINEERING_CONTEXT_P8_EXECUTION.md](./REVIEW_ENGINEERING_CONTEXT_P8_EXECUTION.md) | human gate |

**Baseline (pre-RCX):** 25% diff truncated, 9/40 runs omitted `.md`, prompt p95 164k — see findings § Validation metrics.

**Wave 2 baseline (post-#60):** alembic `0029` on staging; 0 post-merge runs — see findings § Wave 2.
