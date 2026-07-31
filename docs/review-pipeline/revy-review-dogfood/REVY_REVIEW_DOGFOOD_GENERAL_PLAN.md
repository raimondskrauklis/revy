# docs/review-pipeline/revy-review-dogfood/REVY_REVIEW_DOGFOOD_GENERAL_PLAN.md

# Revy review — cross-repo dogfood general plan (RR-W1)

**Baseline:** [REVY_REVIEW_DOGFOOD_FINDINGS.md](./REVY_REVIEW_DOGFOOD_FINDINGS.md) (2026-07-31, peer-review tightened)  
**Validation:** [REVY_REVIEW_DOGFOOD_STAGING_VALIDATION.md](./REVY_REVIEW_DOGFOOD_STAGING_VALIDATION.md)  
**Prerequisite:** Finding-resolution P0–P5 + wave C/D shipped; judge transport #75 merged.

**Thesis:** Closure **mechanisms** work on Revy-repo dogfood; **cross-repo operator trust** fails on ingest races, silent publish skips, stuck resolution cohorts, and diff-hunk false positives. RR-W1 hardens the TenderPro #130 path — extend existing modules; no parallel closure system.

**Gap IDs:** **RR-DG*** in findings; **R0–R5** = program phases below.

**Locked (from findings + peer review):**

| ID | Resolution |
|----|------------|
| RR-Q1 | Finding-resolution mechanisms shipped; cross-repo gate **not** done |
| RR-Q2 | RR-W1 scope: ingest → publish hygiene → resolution stamp → HEAD suppression |
| RR-Q3 | TenderPro #130 is valid staging evidence; no dedicated probe repo required |
| RR-Q4 | **Defer** product merge gate on resolution rate until **R5** |
| RR-Q5 | `head_sha` DB unique index — **R0 decides** (app dedupe may suffice) |
| FR-CS4 Pass 3 supersede | **Out of scope** |
| RR-DG8 | Judge transport — **closed** (#75) |

---

## Cross-cutting (every phase)

- **Tests:** `backend/tests/unit/` per changed service; concurrent `_append_revision` race test required for R1.
- **Reuse:** `github_pull_requests.py`, `github_publish.py`, `github_resolution_metrics.py`, `github_publish_formatter.py`.
- **Observability:** Skip/failure counts in publish **manifest + summary**, not only worker WARNING.
- **i18n:** Backend-only — no new frontend strings.
- **RG-6:** Unchanged.

---

## R0 — Baseline & prerequisites

**Goal:** Lock RR-Q*, capture TenderPro cohort evidence, and **split RR-DG4 hypothesis** before code.

**Scope — in:** Validation memo R0 row; RR-V1–V5 fixtures (RR-V5 = operator matrix items 1, 2, 3, 15, 17); staging DB or pipeline manifest for push showing "Compare blocked: 6" (`closure_blocked_reason`, pairing_revision_ids, `last_seen_revision_id`); decide RR-Q5 (head_sha unique index vs app dedupe only).

**Scope — out:** Product code.

**Deliverables:** RR-Q4/Q5 locked; RR-DG4 root cause tagged (API fail | pairing | line-region | stale stamp); repro protocol for rapid double-push + merge-base push.

**Depends on:** None.

---

## R1 — Revision ingest idempotency

**Goal:** One logical revision per `head_sha`; no `uq_github_pr_revisions_pr_number` abort (**RR-DG3**, **RR-DG11**).

**Scope — in:** (a) Pre-check via existing `_get_revision_for_head_sha` before `_append_revision`; (b) `IntegrityError` on `(pull_request_id, revision_number)` → re-fetch revision for `head_sha`; (c) optional `SELECT … FOR UPDATE` on PR row for `revision_count`; (d) RR-Q5 outcome — migration only if invariant requires DB-enforced `head_sha` uniqueness.

**Scope — out:** Changing GitHub delivery dedupe; supersede lifecycle.

**Deliverables:** Unit test simulating concurrent append (two workers, same/different SHAs); RR-V1 pass.

**Depends on:** R0.

---

## R2 — Publish thread resolve hygiene

**Goal:** Operator sees **why** threads stayed open (**RR-DG1**, **RR-DG7**, **RR-DG9**).

**Scope — in:** Manifest/summary fields: `thread_resolve_skipped_count`, `thread_id_not_found_count`, `resolve_mutation_failed_count`; log GraphQL error body (truncated) on mutation path; optional single retry; **no silent `continue`** when `thread_id is None`.

**Scope — out:** GH-1v2 re-design; foreign/human thread ownership policy (document in R0 if needed).

**Deliverables:** Formatter summary line; unit tests for skip taxonomy; RR-V4 on cohort where R3 stamps `addressed`.

**Depends on:** R1.

---

## R3 — Resolution stamp unblock

**Goal:** Fix pushes stamp `addressed` and resolution rate **> 0%** where operator expects (**RR-DG4**, **RR-DG11**).

**Scope — in:** Per R0 hypothesis: extend **line-region HEAD verification** and existing `head_check_failed` path — **not** duplicate `paths_absent_at_head`; fix stale `closure_blocked_reason`; repair pairing when intermediate revision missing after R1; clear `compare_failed` only when compare API actually failed.

**Scope — out:** FR-Q3 pairing model rewrite; three-way merge simulation.

**Deliverables:** Tests per hypothesis branch; RR-V2 pass on fix-push cohort.

**Depends on:** R0, R1.

---

## R4 — HEAD contradiction suppression & inline recovery

**Goal:** Suppress claims contradicted by file at `head_sha`; recover inline 422 (**RR-DG6**, **RR-DG2**).

**Scope — in:** Post-reconcile hook: if finding claim fails HEAD text check, suppress or downgrade before publish (fixtures from operator matrix items 1–3, 15, 17); inline 422 → line retry or issue-comment fallback.

**Scope — out:** New contents API infrastructure (already exists); Moonshot prompt retrain.

**Deliverables:** Suppression manifest field; unit tests with matrix fixtures; RR-V5 **0/5** false positives on checklist.

**Depends on:** R3 preferred (real fixes stamped); suppression can ship in parallel with R3 if independent.

---

## R5 — Staging sign-off & publish coherence

**Goal:** RR-W1 **PASS** on cross-repo dogfood; confirm publish surfaces coherent (**RR-DG5**, **RR-DG10**).

**Scope — in:** RR-V1–V5 on TenderPro #130 re-run or equivalent; verify successful publish has single `head_sha` across check/comment/inline; document `publish_skipped_not_head` behavior when HEAD advances.

**Scope — out:** Customer repo merges.

**Deliverables:** Validation memo PASS/FAIL; README status; execution index with SHAs; RR-Q4 product gate recommendation.

**Depends on:** R1–R4.

---

## Parking lot

| Item | Notes |
|------|-------|
| Product FAIL check on 0% resolution | RR-Q4 — decide after R5 |
| Bot vs human thread resolve policy | R0/R2 if GraphQL differs |

---

## Open items (R0)

1. Reconcile manifest / DB for "Compare blocked: 6" push.
2. RR-Q5 — `head_sha` unique constraint vs application dedupe.
3. Were 18 skipped threads Revy-owned bot comments on #130?

**Next step:** `create-execution-plan` → `waves/REVY_REVIEW_DOGFOOD_EXECUTION.md` + R0–R5 execution files.
