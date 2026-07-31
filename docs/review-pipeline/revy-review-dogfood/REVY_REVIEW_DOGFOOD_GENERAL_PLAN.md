# docs/review-pipeline/revy-review-dogfood/REVY_REVIEW_DOGFOOD_GENERAL_PLAN.md

# Revy review — cross-repo dogfood general plan (RR-W1)

**Baseline:** [REVY_REVIEW_DOGFOOD_FINDINGS.md](./REVY_REVIEW_DOGFOOD_FINDINGS.md) (2026-07-31)  
**Validation:** [REVY_REVIEW_DOGFOOD_STAGING_VALIDATION.md](./REVY_REVIEW_DOGFOOD_STAGING_VALIDATION.md)  
**Prerequisite:** Finding-resolution P0–P5 + wave C/D shipped; judge transport #75 merged.

**Thesis:** Closure **mechanisms** work on Revy-repo dogfood; **cross-repo operator trust** fails on ingest races, silent publish skips, compare-blocked resolution, and diff-only false positives. RR-W1 hardens the path TenderPro #130 exercised — extend existing modules; no parallel closure system.

**Gap IDs:** **RR-DG*** in findings; **R0–R5** = program phases below.

**Locked (from findings):**

| ID | Resolution |
|----|------------|
| RR-Q1 | Finding-resolution mechanisms shipped; cross-repo gate **not** done |
| RR-Q2 | RR-W1 scope: ingest → publish hygiene → resolution compare → HEAD truth |
| RR-Q3 | TenderPro #130 is valid staging evidence; no dedicated probe repo required for R0–R4 |
| RR-Q4 | Do **not** block merge on resolution rate until R3 proves metric — defer product gate |
| FR-CS4 Pass 3 supersede | **Out of scope** |
| RR-DG8 | Judge transport — **closed** (#75) |

---

## Cross-cutting (every phase)

- **Tests:** `backend/tests/unit/` per changed service; replay TenderPro log scenarios where possible.
- **Reuse:** `github_pull_requests.py`, `github_publish.py`, `github_resolution_metrics.py`, `github_publish_formatter.py` — extend, don't fork.
- **Observability:** Skips and failures visible in publish manifest + summary (operator-readable counts, not only worker WARNING).
- **i18n:** Backend-only — no new frontend strings.
- **RG-6:** Withhold publish without judge outcome — unchanged.

---

## R0 — Baseline & prerequisites

**Goal:** Lock RR-Q* decisions, capture TenderPro #130 baseline metrics, and define RR-V1–V5 pass criteria in the validation memo.

**Scope — in:** Update validation memo with cohort SHAs, log event counts, operator finding matrix pointer; document staging repro protocol (rapid double-push, merge-base push); baseline `judge_json_contract_staging_metrics` / resolution manifest fields for TenderPro PR.

**Scope — out:** Product code changes.

**Deliverables:** Findings decisions RR-Q3/Q4 locked; validation memo R0 row filled; RR-V gates copied to staging validation § sign-off.

**Depends on:** None.

---

## R1 — Revision ingest idempotency

**Goal:** One revision row per `(pull_request_id, head_sha)` — concurrent `synchronize` webhooks must not abort the pipeline (**RR-DG3**).

**Scope — in:** Idempotent `_append_revision` / `_upsert_pull_request` path: catch `uq_github_pr_revisions_pr_number`, return existing revision for same `head_sha`; dedupe by `head_sha` before incrementing `revision_count`; worker task succeeds without IntegrityError retry storm.

**Scope — out:** GitHub delivery dedupe changes (already exists); generation lifecycle supersede logic.

**Deliverables:** Unit tests for concurrent-append race; RR-V1 pass on staging rapid double-push.

**Depends on:** R0.

---

## R2 — Publish thread resolve hygiene

**Goal:** Addressed findings collapse GitHub threads reliably, or the operator sees **why not** (**RR-DG1**, **RR-DG7**).

**Scope — in:** Surface `thread_resolve_skipped_count` + per-reason snippet in publish manifest/summary; optional single retry on GraphQL resolve; log GraphQL error body (truncated); do not inflate "still open" without manifest signal.

**Scope — out:** Re-implementing GH-1v2 triggers; human dismiss UI.

**Deliverables:** Summary line for thread resolve outcomes; unit tests for skip counting; RR-V4 partial (count surfaced even if skips remain).

**Depends on:** R1 (pipeline must complete to publish).

---

## R3 — Resolution compare fallback & summary SHA parity

**Goal:** Fix pushes after merge-base disruption can stamp `addressed` and show non-zero resolution rate; summary and inline share one `head_sha` (**RR-DG4**, **RR-DG5**).

**Scope — in:** When GitHub compare fails for Pass 1, bounded fallback (e.g. prior-published SHA window or HEAD file fetch for line-region check); clear `compare_failed` when fallback succeeds; issue comment + check run + manifest `head_sha` aligned to revision under publish.

**Scope — out:** Full three-way merge simulation; changing FR-Q3 pairing model.

**Deliverables:** Compare-fallback path with tests; RR-V2 + RR-V3 pass on staging fix-push cohort.

**Depends on:** R1.

---

## R4 — HEAD truth & inline recovery

**Goal:** Reduce false positives on long external PRs; recover from inline 422 (**RR-DG6**, **RR-DG2**).

**Scope — in:** Before publish (or at reconcile): verify finding claims against file content at `head_sha` via GitHub contents API where diff context is insufficient; suppress or downgrade findings contradicted by HEAD; inline 422 → retry adjacent line or issue-comment fallback for that group.

**Scope — out:** Re-training Moonshot; full-repo static analysis.

**Deliverables:** HEAD verification hook with tests; false-positive suppression manifest field; RR-V5 improvement on TenderPro-class items.

**Depends on:** R3 (resolution stamp must work for real fixes).

---

## R5 — Staging sign-off

**Goal:** RR-W1 **PASS** on cross-repo dogfood — TenderPro #130 re-run or equivalent external PR.

**Scope — in:** Execute RR-V1–V5; update staging validation sign-off; doc sync (README, finding-resolution cross-link); optional TenderPro operator handoff note.

**Scope — out:** Customer repo code changes.

**Deliverables:** Validation memo sign-off PASS/FAIL; program status line in README; execution index with commit SHAs.

**Depends on:** R1–R4.

---

## Parking lot (unchanged)

| Item | Notes |
|------|-------|
| RR-Q4 product merge gate on resolution rate | Revisit after R5 if metric trustworthy |
| Block merge on 0% resolution | Product — not RR-W1 |

---

## Open item

**RR-Q4** — whether production should NEUTRAL/FAIL check runs when resolution rate is 0% but findings are stale — decide after R5 evidence.

**Next step:** `create-execution-plan` → `waves/REVY_REVIEW_DOGFOOD_EXECUTION.md` + `R0`–`R5` execution files.
