# Review quality R5 — Resolution metrics (G9 owner)

General plan from [REVIEW_QUALITY_FINDINGS.md](./REVIEW_QUALITY_FINDINGS.md) track **M**. **No execution steps.** Same PR as R1 (S1).

**Cross-cutting:** workspace-tenanted; unit tests; feeds R3 “fixed since last review” prose (G9).

**Depends on:** R3 publish snapshots (same PR). **Does not** depend on R7 human dismiss (deferred — [peer review](./REVIEW_QUALITY_PEER_REVIEW.md) M2).

---

## Goal

Measure **resolution rate** at next revision — whether flagged groups were **addressed**, **judge-dismissed**, or **still open**. **Owns `resolution_status`** — R3 formatter reads it (G9).

---

## Scope

**In:**

| Piece | Behavior |
|-------|----------|
| **`resolution_status`** | On `github_finding_groups` at next `synchronize`: `addressed` \| `still_open` \| `judge_dismissed` |
| **Inputs (M2 v1)** | Diff heuristic (file + line region) + group `state=resolved` from judge |
| **G9 hook** | R3 formatter cites counts (“N issues fixed since last push”) |
| **Job** | Background on revision ingest (M1 — v1 counts only) |

**Out:** Human dismiss/ack (R7.6 follow-up); customer analytics dashboard; retroactive pre-ship runs.

**Heuristic (locked M2):**

| Status | Rule |
|--------|------|
| `judge_dismissed` | Group `state=resolved` from judge outcome |
| `addressed` | Diff on next revision touches `file_path` + line region (join latest finding `start_line`/`end_line`) |
| `still_open` | Else |

**Execution order (same PR):** `summary_json` column (G8) → resolution job on `synchronize` → G9 formatter hook.

---

## Deliverables

1. On second revision, prior active groups get `resolution_status`.
2. R3 publish prose uses resolution counts (G9).
3. Unit tests: judge resolved → `judge_dismissed`; line changed → `addressed`; unchanged → `still_open`.
4. Pipeline trace unchanged — metrics derived, not LLM step.

---

## Depends on

R3 `summary_json` snapshot; two revisions on staging PR.

---

## Next

Section in `waves/REVIEW_QUALITY_EXECUTION.md`. Pre-execution locks: [peer review](./REVIEW_QUALITY_PEER_REVIEW.md).
