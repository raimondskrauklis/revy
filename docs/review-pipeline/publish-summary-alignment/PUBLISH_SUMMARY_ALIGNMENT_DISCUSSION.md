# Publish summary alignment — discussion log

**Date:** 2026-07-29  
**Purpose:** Lock product direction **before** implementation. No execution steps.

**Participants:** Operator + agent (post PR #61 merge, RCX P6+P7 on `main`).

---

## Problem statement (operator)

After each push/review, developers read the **issue comment** as the primary triage surface. Today:

- The comment is **replaced** each publish (correct — snapshot at HEAD).
- Review input uses the **full PR diff** each run (correct — no cross-push LLM memory).
- **But** the issue comment only lists **this generation’s** publishable findings, while the **check run** already shows **two blocks** (this generation + still open on PR).
- **Confidence** and **merge recommendation** on the issue comment are computed from generation-only groups — so the comment can say “ready to merge” while prior-revision findings remain **active** in DB, listed on the check, and visible as **open inline threads**.

Operator intent: **full cycle in one PR** — align summary with **comments solved / still open**; monitor RCX + judge-json-contract staging validations **in parallel** (no blocking).

---

## What finding-resolution already decided

| Decision | Source | Shipped where |
|----------|--------|---------------|
| Two-block **check** summary | FR-Q7, P4.2 | `format_summary_comment` in `build_check_run_summary` |
| Issue comment = generation-only | P4 execution note | `build_pr_review_comment_fallback` — **intentional defer** |
| Inline = generation publishable only | FR-Q7 | `inline_publish_findings_statement` |
| Thread collapse on fix | GH-1v2 | `_fingerprints_to_resolve_inline_threads` on publish |

**Conclusion:** FR-Q7 was **half-shipped**. RG-14 / FR-Q16 is the **completion** of the same product contract on the issue comment — not a new policy debate.

---

## Options considered

| Option | Pros | Cons | Verdict |
|--------|------|------|---------|
| **A. Mirror two-block on issue comment** | Matches check; Greptile-class triage; no false “ready to merge” | Longer comment; Moonshot must format both blocks | **Adopt (PSA-D1)** |
| **B. Tighten closure so generation = PR active** | Shorter comment | Hides legit still-open; fights Moonshot re-report; closure is separate program | **Reject** |
| **C. Generation-only but fix confidence only** | Small diff | Findings table still omits prior open — threads vs summary mismatch remains | **Reject alone** |
| **D. Append history each push** | Full audit trail | Violates snapshot semantics (RG-Q1) | **Reject** |

---

## Locked decisions (PSA-D*)

| ID | Decision |
|----|----------|
| **PSA-D1** | Issue comment includes **same two blocks** as check: `### This generation` + `### Still open on PR` (reuse `format_summary_comment` or shared builder). |
| **PSA-D2** | **Verdict fields** — confidence, merge recommendation, files needing attention, security/important-files sections — use **PR-wide active** (`pr_active_groups` when present). Generation block carries per-push findings; PR block carries continuity. |
| **PSA-D3** | **G9 “Since last push”** and resolution metrics block stay tied to **this generation’s** publishable groups (`ctx.groups`) — transitions are per push pair, not PR lifetime. |
| **PSA-D4** | **Inline posting** unchanged — generation publishable only (FR-Q7). Summary alignment does not widen inline scope. |
| **PSA-D5** | **Moonshot path** must match fallback: PR-wide verdict numbers + both finding sets. **`ISSUE_COMMENT_FORMAT_SYSTEM_PROMPT` rewrite required** in P1 (step 7 → two-block headings). |
| **PSA-D6** | **No new closure/reconcile logic** in this program — display parity only. Trust GH-1v2 + finding-resolution for thread state. |
| **PSA-D7** | Flip `test_build_pr_review_comment_fallback_generation_only_not_pr_block` → expect `### Still open on PR` and prior file path when `pr_active_groups` has extras. |
| **PSA-D8** | Staging validation runs **in parallel** with RCX pass 2 and judge-json-contract memo — separate checklist rows; same dogfood PR (#61 class) acceptable. |
| **PSA-D9** | Branch: `feat/publish-summary-alignment` from **`main`** after #61 merge. No schema migration. |
| **PSA-D10** | **Info findings UX:** flat two-block tables via `format_summary_comment`; **drop** generation-only info `<details>` collapse — matches check run; update `greptile_shape` / `collapses_info` tests in P0. |
| **PSA-D11** | **`summary_json`:** `confidence` + `active_count` from PR-wide `verdict_groups`; add `generation_active_count` + `pr_active_count` for trace. |
| **PSA-D12** | **`compute_check_conclusion(groups)`** stays generation-scoped — advisory check may show `success` while PR-wide merge copy warns; **out of scope**. |

---

## Open questions (resolved)

| Q | Resolution |
|---|------------|
| Re-open FR-Q7? | **No** — extend it; FR-Q16 → **in flight** under this program. |
| Change review diff to push-only? | **No** — full PR diff stays; only **display** alignment. |
| Block merge on PR-wide open? | **No change** — advisory **check conclusion** stays generation-scoped (PSA-D12); issue **merge recommendation** PR-wide. |
| Info collapse in block 1? | **Flat tables** — PSA-D10; drop `<details>` info collapse. |
| `summary_json` fields? | PR-wide `confidence`/`active_count` + generation/pr counts — PSA-D11. |

---

## Next step

Baseline [PUBLISH_SUMMARY_ALIGNMENT_FINDINGS.md](./PUBLISH_SUMMARY_ALIGNMENT_FINDINGS.md) → [GENERAL_PLAN](./PUBLISH_SUMMARY_ALIGNMENT_GENERAL_PLAN.md) → [execution waves](./waves/PUBLISH_SUMMARY_ALIGNMENT_EXECUTION.md) → architecture peer review (2026-07-29) → `phase-execution`.
