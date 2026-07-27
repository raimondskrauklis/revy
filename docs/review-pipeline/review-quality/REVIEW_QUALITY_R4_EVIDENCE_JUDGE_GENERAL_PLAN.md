# Review quality R4 — Evidence + grounding judge

General plan from [REVIEW_QUALITY_FINDINGS.md](./REVIEW_QUALITY_FINDINGS.md) track **E**. **No execution steps.** Same PR as R1 (S1).

**Cross-cutting:** extend pipeline `judge` artifacts; `evidence_snippet` on findings; hand-written Alembic; unit tests.

**Depends on:** R1 judge prompt/response capture (same PR); **review-pipeline R5 reconcile** (`github_reconcile`, fingerprints, groups) — **not** review-quality R5 metrics.

---

## Goal

Findings carry the **code excerpt** used in review; judge verifies **claim vs evidence** (entailment), not message alone — fewer false positives on publish; meaningful Sonnet 5 vs Opus tuning.

---

## Scope

**In:** `github_findings.evidence_snippet TEXT NULL` (E1); populate from diff hunk or top retrieval chunk at parse time; extend `_build_judge_prompt` with snippet; grounding instruction — dismiss / weaken when not entailed (E2); pipeline trace links finding → evidence → judge raw response.

**Out:** Multi-model jury (Track A); devil’s advocate agent; evidence in GitHub summary table (G7 off); Reviewer `FindingRow` evidence column.

**Locked:** E1 column; E2 grounding in judge prompt.

---

## Deliverables

1. New findings persist non-null `evidence_snippet` when diff/retrieval supplied context for file/line.
2. Judge prompt includes snippet; dismissed when claim contradicts snippet (unit fixtures).
3. Pipeline trace shows evidence + judge I/O per escalated group.
4. Staging: fewer false positives vs pre-grounding on known fixture.
5. Publish filters `active` groups only — grounded dismiss → not in inline/summary.

---

## Depends on

- R1 trace + diff-first context (same PR)
- **Review-pipeline R5** reconcile job — stable groups + **D10** fingerprint (same PR)

---

## Next

Section in `waves/REVIEW_QUALITY_EXECUTION.md`.
