# Publish summary alignment — execution index

**Baseline:** [PUBLISH_SUMMARY_ALIGNMENT_FINDINGS.md](../PUBLISH_SUMMARY_ALIGNMENT_FINDINGS.md)  
**General plan:** [PUBLISH_SUMMARY_ALIGNMENT_GENERAL_PLAN.md](../PUBLISH_SUMMARY_ALIGNMENT_GENERAL_PLAN.md)  
**Discussion:** [PUBLISH_SUMMARY_ALIGNMENT_DISCUSSION.md](../PUBLISH_SUMMARY_ALIGNMENT_DISCUSSION.md)

**Branch:** `feat/publish-summary-alignment` from `main` (post PR #61).

**Peer review:** Architecture peer review 2026-07-29 — critical/high gaps incorporated into P0/P1.

## Locked decisions (all phases)

- PSA-D1–D12 — see discussion doc.
- Reuse `format_summary_comment` for both check and issue comment findings sections.
- `verdict_groups(ctx)` → `pr_active_groups if not None else groups`.
- No Alembic; no reconcile/closure changes; `compute_check_conclusion` unchanged (PSA-D12).
- Inline scope unchanged.

## LOOP order

| Phase | Focus | File | Status |
|-------|--------|------|--------|
| P0 | Contract + fallback + verdict + metrics markers | [P0](./PUBLISH_SUMMARY_ALIGNMENT_P0_EXECUTION.md) | pending |
| P1 | Moonshot system/user prompt + parity tests | [P1](./PUBLISH_SUMMARY_ALIGNMENT_P1_EXECUTION.md) | pending |
| P2 | Staging validation + doc sync | [P2](./PUBLISH_SUMMARY_ALIGNMENT_P2_EXECUTION.md) | pending |

**Next:** `phase-execution` — peer-review blockers cleared.

**Related programs after ship:** RCX / judge-json-contract staging pass 2 (parallel).
