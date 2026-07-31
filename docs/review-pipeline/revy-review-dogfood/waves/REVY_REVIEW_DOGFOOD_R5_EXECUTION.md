# docs/review-pipeline/revy-review-dogfood/waves/REVY_REVIEW_DOGFOOD_R5_EXECUTION.md

# R5 — Staging sign-off & doc sync (execution)

Phase **R5** of [REVY_REVIEW_DOGFOOD_GENERAL_PLAN.md](../REVY_REVIEW_DOGFOOD_GENERAL_PLAN.md). Baseline: [REVY_REVIEW_DOGFOOD_FINDINGS.md](../REVY_REVIEW_DOGFOOD_FINDINGS.md) § Experiment / verification. **R5 only.**

**Goal:** RR-V1–V5 PASS on staging (or documented partial with owner); RR-Q4 recommendation; program README status closed.

**Status:** **done** `b8a589e` on [#80](https://github.com/raimondskrauklis/revy/pull/80) — 10 review runs; RR-V1–V4/judge/closure PASS; RR-V5 manual pytest matrix documented. See [staging validation memo](../REVY_REVIEW_DOGFOOD_STAGING_VALIDATION.md).

## Decisions locked for R5

- Staging target: **`raimondskrauklis/revy` [PR #80](https://github.com/raimondskrauklis/revy/pull/80)** — multi-push probe protocol (defect → structural fix → delete defect → empty pushes).
- RR-Q4: emit **recommendation** only — **defer** product merge gate on resolution rate; use DB metrics (`--rr-v-gate`) as operator health signal.
- Judge transport (RR-DG8): no re-verify unless regression suspected.
- RR-DG5 / RR-DG10: verify on successful publish cohort — summary/inline/check `head_sha` parity (RR-V3); document any `publish_skipped_not_head` when operator pushes ahead of in-flight publish.

## Out of scope for R5

- Further code unless RR-V failure requires hotfix subphase (document as R5.x)

---

## R5.1 — Staging RR-V1–V5 execution

**What:** Operator runs repro protocol from R0.4 on staging after R1–R4 deploy; fill validation memo pass/fail per gate (authority: findings § Experiment / verification).

| Gate | Pass |
|------|------|
| **RR-V1** | Rapid double-push same SHA → one revision row per `head_sha`; no IntegrityError |
| **RR-V2** | After fix push, resolution rate **> 0%** on line-edit cohort (R0 manifest confirms stamp path) |
| **RR-V3** | Successful publish: summary `head_sha` == revision `head_sha` == inline batch |
| **RR-V4** | Thread resolve skip count **0** or manifest shows `thread_id_not_found` / `resolve_mutation_failed` breakdown |
| **RR-V5** | Matrix items **1, 2, 3, 15, 17** — **0/5** false positives published |

**Files:** `REVY_REVIEW_DOGFOOD_STAGING_VALIDATION.md`

**Deliverable:** Signed § Sign-off table with date + deploy SHA — **done** 2026-07-31 (`b8a589e`, rev 10).

---

## R5.2 — RR-Q4 recommendation

**What:** One paragraph in findings + validation memo: whether Revy product FAIL on 0% resolution should block app merge for cross-repo dogfood.

**Files:** `REVY_REVIEW_DOGFOOD_FINDINGS.md`, `REVY_REVIEW_DOGFOOD_STAGING_VALIDATION.md`

**Deliverable:** RR-Q4 status `locked` with **`defer`** recommendation — recorded in findings + validation memo.

---

## R5.3 — Doc sync & program close

**What:** Update program README phase table to **done**; execution index Status column + **commit SHA per phase**; optional `docs/review-pipeline/finding-resolution/README.md` cross-link; archive `active_program` in review-context when next program starts.

**Files:** `docs/review-pipeline/revy-review-dogfood/README.md`, `waves/REVY_REVIEW_DOGFOOD_EXECUTION.md`, `docs/review-pipeline/README.md`, `.revy/review-context.json` (if superseded)

**Deliverable:** **done** — README + execution index updated; finding-resolution cross-link updated.

---

## R5.4 — post-finish-gap-pass (optional)

**What:** Invoke `@post-finish-gap-pass` against shipped code vs R0–R4 execution files; fix doc-only gaps ≤ 30 min.

**Files:** Program docs only unless trivial code gap found.

---

**Phase gate** (human):

- **RR-V1** PASS (ingest)
- **RR-V3** PASS on at least one successful publish (surface coherence — RR-DG5/10)
- **RR-V4** PASS or manifest breakdown acceptable (thread taxonomy)
- **RR-V2** and **RR-V5** PASS or documented partial with follow-up issue
- RR-Q4 recommendation recorded

**Program complete** when R5.3 merged to `main`. **Validation complete** on [#80](https://github.com/raimondskrauklis/revy/pull/80) `b8a589e` — merge PR pending operator.
