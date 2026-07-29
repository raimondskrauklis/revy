# Publish summary alignment — general plan

**Baseline:** [PUBLISH_SUMMARY_ALIGNMENT_FINDINGS.md](./PUBLISH_SUMMARY_ALIGNMENT_FINDINGS.md) (2026-07-29)  
**Discussion:** [PUBLISH_SUMMARY_ALIGNMENT_DISCUSSION.md](./PUBLISH_SUMMARY_ALIGNMENT_DISCUSSION.md) — PSA-D1–D12 locked.

**Prerequisite:** `main` with finding-resolution, generation lifecycle, GH-1v2, RCX P6+P7 (#61).

**Thesis:** Developers see **one honest story** on GitHub — issue comment, check summary, and inline thread state agree on what is **new this push**, what is **still open on the PR**, and whether merge looks safe.

**Gap IDs:** **RG-14** / **FR-Q16** → closed when P2 ships.

**Peer review:** Architecture peer review (2026-07-29) — gaps folded into P0/P1 execution.

---

## Locked decisions (PSA-D*)

| ID | Decision |
|----|----------|
| PSA-D1 | Issue comment: two-block findings (`format_summary_comment`) |
| PSA-D2 | Verdict fields use PR-wide `pr_active_groups` (incl. `_confidence_rationale`) |
| PSA-D3 | G9 + resolution metrics stay generation-scoped |
| PSA-D4 | Inline = generation publishable only |
| PSA-D5 | Moonshot user + **system** prompt match fallback (system rewrite **required** P1) |
| PSA-D6 | No new closure/reconcile logic |
| PSA-D10 | Flat two-block tables; drop info `<details>` collapse |
| PSA-D11 | `summary_json` PR-wide confidence/counts + generation/pr trace fields |
| PSA-D12 | `compute_check_conclusion` generation-scoped — out of scope |

---

## Cross-cutting (every phase)

- **Unit tests** — formatter contract; greptile/collapse test updates; merge-regression test; parity check ≡ issue.
- **No migration** — formatter-only.
- **i18n** — backend-only; no new UI strings.
- **Trace** — `summary_json` fields per PSA-D11 in P0.
- **Greptile / Bugbot refs** — P0 first commit.

---

## P0 — Product contract + fallback parity

**Goal:** Deterministic issue comment and check share two-block findings; all verdict copy PR-wide; metrics insert markers fixed.

**Scope — in:** `verdict_groups(ctx)`; fallback `format_summary_comment`; PSA-D10 flat tables; PR-wide verdict + rationale + `summary_json`; `_insert_resolution_metrics_block` markers; greptile/collapse test updates; headline merge-regression test.

**Scope — out:** Moonshot; `compute_check_conclusion`; staging memo.

**Deliverables:** Fallback + check display aligned; tests green; PR review context.

**Depends on:** `main` post-#61.

---

## P1 — Moonshot path + parity tests

**Goal:** LLM-formatted issue comment meets same product bar as P0 fallback.

**Scope — in:** `_build_issue_comment_user_prompt`; **required** `ISSUE_COMMENT_FORMAT_SYSTEM_PROMPT` rewrite; simplified product bar (both headings when PR active); check ≡ issue two-block substring test; Moonshot mocks updated.

**Scope — out:** Moonshot review ingest; check conclusion.

**Deliverables:** Moonshot success/fallback paths pass product bar tests.

**Depends on:** P0.

---

## P2 — Staging validation + doc sync

**Goal:** Operator sign-off; close RG-14 / FR-Q16; document PSA-D12 on staging.

**Scope — in:** Validation memo; README status; corpus cross-links; PRODUCT_PATTERNS row; inline vs check conclusion notes.

**Scope — out:** Production sign-off; changelog.

**Deliverables:** Validation memo filled; program **shipped** on branch merge.

**Depends on:** P0, P1.

---

## Out of scope

Push-only review diff; append comment history; new closure rules; **`compute_check_conclusion` PR-wide alignment** (PSA-D12); workspace analytics; email digest.

---

## Next step

**`phase-execution`** from [PUBLISH_SUMMARY_ALIGNMENT_EXECUTION.md](./waves/PUBLISH_SUMMARY_ALIGNMENT_EXECUTION.md) on `feat/publish-summary-alignment`.
