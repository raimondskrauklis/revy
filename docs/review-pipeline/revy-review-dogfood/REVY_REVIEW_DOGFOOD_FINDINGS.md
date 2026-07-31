# Revy review — cross-repo dogfood findings

**Date:** 2026-07-31  
**Purpose:** Baseline for the **next Revy product pass** after finding-resolution shipped — gaps exposed by staging dogfood on an **external repo** (TenderPro), not Revy self-dogfood. **No execution steps.**

**Trigger:** [TenderPro PR #130](https://github.com/raimondskrauklis/tender_pro/pull/130) super-admin dashboard wave 1 — 12+ Revy revisions, heavy fix/push iteration. Operator validation: `misc/SUPER_ADMIN_DASHBOARD_STAGING_VALIDATION.md` · worker log: `misc/tenderprolog.txt`.

**Authority:** [finding-resolution FINDINGS](../finding-resolution/FINDING_RESOLUTION_FINDINGS.md) · [finding-resolution-dogfood](../finding-resolution-dogfood/README.md) · [judge transport validation](../judge/JUDGE_TRANSPORT_RELIABILITY_STAGING_VALIDATION.md) · code read on `main` (`75aa856`).

---

## Build principles

1. **Mechanism proof ≠ operator trust** — FR-DG1 PASS on Revy repo does not mean resolution rate works on a 12-revision customer PR with merge commits.
2. **Verify against HEAD file** — diff-only review produces false positives; operators waste cycles on fixed code.
3. **Ingestion before intelligence** — duplicate revision insert aborts the pipeline; no amount of judge quality helps.
4. **Publish hygiene is product** — skipped thread resolve and stale summary SHA erode the merge gate.
5. **Reuse finding-resolution infra** — compare_failed, Option B resolve, RG-6 — extend; do not fork parallel closure systems.

---

## Terminology

| Term | Meaning |
|------|---------|
| **Cross-repo dogfood** | Staging Revy reviewing a non-`revy` installation repo |
| **Resolution rate** | `resolution_rate_pct` in publish manifest — % prior active groups marked addressed/dismissed this push |
| **Compare blocked** | `closure_blocked_reason=compare_failed` — GitHub compare could not produce reliable patch for Pass 1 |
| **Thread resolve skip** | `github_publish_resolve_inline_thread_skipped` — Option B / GH-1 path did not resolve GitHub thread |

---

## Summary

**Verified (positive):** Judge transport hardening ([#75](https://github.com/raimondskrauklis/revy/pull/75)) works cross-repo — `judge_llm_request_started` / `judge_llm_request_completed` on TenderPro rev 12 (`tenderprolog.txt` L6–8, ~2.8s direct Anthropic).

**Verified (TenderPro app):** Operator matrix — **no verified open app bugs** on `d915b4e`; 3/3 active Revy rev-12 items **false or already fixed** (missing `or_` import, SystemStatusBar props, export label).

**Verified (Revy product gaps):**

| Area | Symptom on #130 |
|------|-----------------|
| Resolution tracking | **0.0% resolution rate**; **6 compare-blocked** groups after `origin/main` merge |
| Publish hygiene | **18×** `github_publish_resolve_inline_thread_skipped`; **1×** inline 422 skip |
| PR ingest | **IntegrityError** `uq_github_pr_revisions_pr_number` rev **13** on rapid `d915b4e` + `999ad17` pushes |
| Summary UX | Rev 12 summary pinned `b4ba498` while inline comments on `999ad17` |
| Review accuracy | High false-positive rate on items already fixed in HEAD |

**Conclusion:** The **original finding-resolution problem is largely solved in code** for Revy-repo cohorts; **cross-repo operator experience** still fails the merge gate. One more pass (**RR-W1**) should target ingest + publish hygiene + HEAD-aware reconciliation — not re-litigate Pass 1/2 mechanics.

---

## Case study — TenderPro PR #130

| Field | Value |
|-------|-------|
| External repo | `raimondskrauklis/tender_pro` |
| PR | [#130](https://github.com/raimondskrauklis/tender_pro/pull/130) |
| Branch | `feat/super-admin-dashboard-wave1` |
| Revy revisions | 12+ (operator session 2026-07-31) |
| Feature tip | `d915b4e` (code) · `999ad17` (doc-only) |
| App merge readiness | **PASS** (operator) |
| Revy staging PASS | **FAIL** (resolution + ingest) |

---

## Gap catalog

| ID | Gap | Severity | Status | Evidence |
|----|-----|----------|--------|----------|
| **RR-DG1** | Inline thread resolve skipped at publish | **high** | open | 18× warning in `tenderprolog.txt` L20–56; `github_publish.py:721-730` logs and continues |
| **RR-DG2** | Inline comment post 422 skipped | medium | open | `tenderprolog.txt` L64–65; `github_publish.py:1443-1454` |
| **RR-DG3** | Duplicate PR revision on concurrent synchronize | **high** | open | `tenderprolog.txt` L114–116 — `uq_github_pr_revisions_pr_number` rev 13; `_append_revision` (`github_pull_requests.py:196-213`) has no upsert/idempotency |
| **RR-DG4** | Compare blocked after merge-base disruption | **high** | open | Summary "Compare blocked: 6 group(s)" + 0% resolution after `f1e6325` merge `origin/main`; `github_resolution_metrics.py` + `closure_blocked_reason=compare_failed` |
| **RR-DG5** | Summary `head_sha` lags inline generation | medium | open | Rev 12 summary `b4ba498` vs inline on `999ad17` (`SUPER_ADMIN_DASHBOARD_STAGING_VALIDATION.md`) |
| **RR-DG6** | False positives on HEAD file content | **high** | open | 3/3 active rev-12 items operator-verified false/fixed; reviewer/judge uses diff context not full file at `head_sha` |
| **RR-DG7** | Resolution UX — fixed code, open threads | medium | open | Operator notes (was in finding-resolution README); multi-push iteration cost |
| **RR-DG8** | Judge transport (cross-repo) | — | **verified fixed** | `judge_llm_request_*` + publish complete rev 12; [#75](https://github.com/raimondskrauklis/revy/pull/75) |

---

## Architecture (verified)

```text
[TenderPro push]
  → github webhook synchronize (possibly concurrent)
  → _append_revision (RR-DG3 race)
  → index + review + reconcile + judge (RR-DG8 OK)
  → apply_resolution_status_for_synchronize (RR-DG4 compare_failed)
  → publish: inline post (RR-DG2) + thread resolve (RR-DG1) + summary (RR-DG5)
```

| Layer | File | RR-DG |
|-------|------|-------|
| Revision ingest | `github_pull_requests.py` | RR-DG3 |
| Pass 1 compare | `github_resolution_metrics.py`, `github_compare_patches.py` | RR-DG4 |
| Publish inline | `github_publish.py` | RR-DG1, RR-DG2 |
| Summary formatter | `github_publish_formatter.py` | RR-DG4, RR-DG5 |
| Judge transport | `anthropic_review.py` | RR-DG8 (fixed) |

---

## What exists vs what dogfood exposed

| Layer | Shipped (finding-resolution) | Cross-repo #130 |
|-------|------------------------------|-----------------|
| Pass 1 line-region + deletion | wave C/D | Compare **failed** after main merge — stamp blocked |
| Pass 2 `absent_and_addressed` | P1/P2 | Never reached for blocked cohort |
| Inline Option B resolve | P4 / GH-1v2 | **Skipped** 18× — threads stay open |
| Resolution rate in summary | P3 / RQ6 | **0%** despite fixes pushed |
| Revision per push | R2 | **Race** on rapid pushes |
| Judge LLM | R5 + transport #75 | **Works** |

---

## Root cause sketches

### RC-1 — Revision append is not idempotent (RR-DG3)

Concurrent `synchronize` webhooks (or push + webhook overlap) both call `_append_revision` with incremented `revision_count`. Second insert hits `uq_github_pr_revisions_pr_number`. PR **create** handles `IntegrityError`; **revision append does not** — task retries/fails (`github_webhook_task_failed`).

### RC-2 — Thread resolve failures are silent (RR-DG1)

`resolve_review_threads_for_addressed_groups` catches HTTP/ServiceUnavailable errors per fingerprint and logs `github_publish_resolve_inline_thread_skipped` without surfacing count in publish summary. Operator sees "still open" with no actionable Revy signal.

### RC-3 — Merge commit breaks compare pairing (RR-DG4)

After merging `origin/main` into feature branch (`f1e6325`), GitHub compare base for resolution Pass 1 no longer aligns with operator mental model of "I fixed these findings." Groups get `compare_failed`; resolution rate stays 0% even when code is correct.

### RC-4 — Review model reads diff, not HEAD truth (RR-DG6)

Revy flags `or_` missing when import exists on `999ad17`; SystemStatusBar "missing props" when optional props only. Operator must manually triage — undermines merge gate on long PRs.

---

## Advice — recommended next wave (RR-W1)

| Priority | Track | Addresses | Approach sketch |
|----------|-------|-----------|-----------------|
| P0 | **Revision idempotency** | RR-DG3 | Upsert revision by `(pull_request_id, head_sha)` or catch unique violation → fetch existing rev |
| P0 | **Thread resolve diagnostics** | RR-DG1 | Fail-soft but **count** skips in summary; optional retry; log GraphQL error body |
| P1 | **Merge-base compare fallback** | RR-DG4 | When compare fails post-merge, fallback compare window or HEAD file fetch for Pass 1 |
| P1 | **Summary SHA parity** | RR-DG5 | Issue comment + check run always reflect same `head_sha` as inline batch |
| P2 | **HEAD file verification** | RR-DG6 | Reconcile/judge/summary generation: verify finding against file at `head_sha` before publish |
| P2 | **Inline 422 recovery** | RR-DG2 | Retry with line adjustment or degrade to issue-comment-only for that finding |

**Defer:** Re-litigating FR-CS4 Pass 3 supersede — orthogonal to this dogfood session.

---

## Decisions registry

| ID | Question | Status | Resolution |
|----|----------|--------|------------|
| **RR-Q1** | Is finding-resolution "done"? | **locked** | **Mechanisms shipped**; cross-repo operator gate **not** done |
| **RR-Q2** | Next pass scope? | **locked** | **RR-W1** — ingest + publish hygiene + HEAD truth (findings above) |
| **RR-Q3** | Use external repo for staging probes? | **locked** | TenderPro #130 validated for RR-W1; no dedicated probe repo required |
| **RR-Q4** | Block merge on 0% resolution rate? | **open** | Defer until R5 — see general plan |

---

## Parking lot

| Item | Notes |
|------|-------|
| TenderPro probe code on Revy | N/A — dogfood on customer's real PR |
| RTU gateway fallback | Closed partial PASS — unrelated |
| Analytics KPI layout nits | TenderPro defer — not Revy |

---

## Experiment / verification (RR-W1 gates)

| Gate | Pass criteria |
|------|---------------|
| RR-V1 | Rapid double-push on staging PR → **one** revision row per `head_sha`; no IntegrityError |
| RR-V2 | After fix push, resolution rate **> 0%** on cohort with line edits |
| RR-V3 | Publish summary `head_sha` == latest inline comment commit |
| RR-V4 | Thread resolve skip count **0** or surfaced in summary with reason |
| RR-V5 | Re-run TenderPro-class PR — false positive rate drop on HEAD-verified items |

---

## References

| Source | Path |
|--------|------|
| Operator validation (TenderPro) | `misc/SUPER_ADMIN_DASHBOARD_STAGING_VALIDATION.md` |
| Worker log slice | `misc/tenderprolog.txt` |
| Revision model | `backend/app/models/github_pull_request.py` |
| Thread resolve | `backend/app/services/github_publish.py:680-730` |
| Compare failed | `backend/app/services/github_resolution_metrics.py` |
| Prior dogfood | [finding-resolution-dogfood POST_VALIDATION](../finding-resolution-dogfood/FINDING_RESOLUTION_DOGFOOD_POST_VALIDATION_FINDINGS.md) |
