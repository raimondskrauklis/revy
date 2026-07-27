# Review quality R3 — GitHub publish (Greptile-shaped)

General plan from [REVIEW_QUALITY_FINDINGS.md](./REVIEW_QUALITY_FINDINGS.md) track **G**. **No execution steps.** Same PR as R1 (S1).

**Cross-cutting:** extend `github_publish` + pipeline `publish` artifact; deterministic confidence (G2); unit tests; **no mermaid** (G4).

**Depends on:** R1 diff-first findings + trace (same PR).

---

## Goal

GitHub PR comment + check run = **primary triage surface** — Greptile-shaped summary ([#35](https://github.com/raimondskrauklis/revy/pull/35) / [#36](https://github.com/raimondskrauklis/revy/pull/36)): narrative, confidence, files needing attention, important files changed, revision-aware delta.

---

## Scope

**In:**

| Piece | Deliverable |
|-------|-------------|
| **Formatter** | `build_pr_review_comment()` — narrative + themed bullets (G5); publisher LLM with structured in/out; fallback to table-only |
| **Confidence** | 0–5 deterministic from severities + prior-pass delta (G2) |
| **G3 split bodies** | **Check run** = compact (verdict + confidence + severity table); **issue comment** = full Greptile narrative |
| **Sections** | Files needing attention; `<details>` important-files table; metadata footer (`head_sha`, pass #, `@revy review`, Revy run link) |
| **Delta prose** | “Fixed since last review” reads **`resolution_status`** from R5 (G9); fingerprint snapshot secondary |
| **Snapshot** | `summary_json` on publish job for next revision (G8) |
| **Idempotency** | Update in place per `head_sha` (R6-Q1) |

**Locked:** G1 extend not replace; G6 P2 inline off; G7 message column off.

**Out:** mermaid; email digest; Reviewer UI changes.

---

## Deliverables

1. PR issue comment matches Greptile section shape (minus mermaid) on staging dogfood PR.
2. Check run stays under GitHub size limits (G3).
3. Confidence + verdict update on each `synchronize` re-publish.
4. Zero findings → confidence 5/5 + “No files require special attention.”
5. Formatter failure → R6 table fallback; publish completes.
6. Publish snapshot stored for next revision delta.

---

## Depends on

R1 pipeline trace; R5 `resolution_status` for G9 prose (implement R5 before or with R3 formatter hook in same PR).

---

## Next

Section in `waves/REVIEW_QUALITY_EXECUTION.md`.
