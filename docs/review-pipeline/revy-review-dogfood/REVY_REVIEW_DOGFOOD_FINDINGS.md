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
| **RR-DG4** | Resolution cohort stuck — 0% rate / compare-blocked summary | **high** | open — **R0 tag locked** | Primary tag **`stale_closure_blocked`** (validation memo § R0.2); worker log compare 200 at `b4ba498`/`d915b4e`/`999ad17`; secondary `pairing_gap` + RR-DG11 |
| **RR-DG5** | Summary `head_sha` lags inline generation | medium | open — **likely symptom** | Rev 12 summary `b4ba498` vs inline on `999ad17`; intra-job publish uses single `job.head_sha` — aligns with **no successful publish** for newer SHA after rev-13 IntegrityError (RR-DG3), not intra-job drift |
| **RR-DG6** | False positives on HEAD file content | **high** | open — **reframed** | Contents API already used at `head_sha` (log + engineering context); false positives are **reviewer/judge reasoning on diff hunks**, not missing HEAD fetch — needs post-reconcile **suppression** |
| **RR-DG7** | Resolution UX — fixed code, open threads | medium | open | Operator notes; multi-push iteration cost |
| **RR-DG8** | Judge transport (cross-repo) | — | **verified fixed** | `judge_llm_request_*` + publish complete rev 12; [#75](https://github.com/raimondskrauklis/revy/pull/75) |
| **RR-DG9** | Silent skip when `thread_id` is None | medium | open | `github_publish.py:712-713` — `continue` with no log or manifest count |
| **RR-DG10** | `publish_skipped_not_head` / mixed GitHub surfaces | medium | open | HEAD advances mid-publish → check/comment at older generation while inline partial |
| **RR-DG11** | Intermediate revision gap after failed ingest | medium | open | Failed rev 13 leaves hole; `get_intermediate_revision_ids_between` / pairing may exclude groups from restamp |

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

### RC-2 — Thread resolve failures under-reported (RR-DG1, RR-DG9)

18 skips in log follow GraphQL **200 OK** then `github_publish_resolve_inline_thread_skipped` — likely `resolveReviewThread` GraphQL errors → `ServiceUnavailableError` (`github_api.py`). Separate path: `thread_id is None` at `github_publish.py:712-713` skips **silently** (no log, no manifest). R2 must taxonomy: `resolve_mutation_failed` vs `thread_id_not_found`.

### RC-3 — Resolution cohort stuck — multiple hypotheses (RR-DG4, RR-DG11)

**Not confirmed:** GitHub compare API failed for TenderPro fix pushes (worker log shows 200 compare for `b4ba498…d915b4e` and `b4ba498…999ad17`). Plausible causes:

1. **Stale** `closure_blocked_reason=compare_failed` from an earlier sync
2. **Pairing gap** — `last_seen_revision_id` not in `pairing_revision_ids` after merge or skipped rev 13
3. **Line-region miss** — compare succeeds but fix outside prior→new diff window (`patch_touches_line_region`)

Existing partial fallback: `paths_absent_at_head` + `head_check_failed` when compare fails (`github_resolution_metrics.py:291-307`). R3 extends line-region HEAD check — does not duplicate path-absence logic.

### RC-4 — False positives are reasoning, not missing HEAD fetch (RR-DG6)

Review pipeline already fetches file contents at `head_sha`. Operator matrix items 1–3 false/fixed on `999ad17` need **post-reconcile suppression** when claim contradicts HEAD text — not a new contents API.

### RC-5 — Summary SHA lag is failed publish, not publish bug (RR-DG5)

Single publish job uses `job.head_sha` for check run, issue comment, and inline posts. Stale summary on older SHA when newer pushes fail ingest (RR-DG3) or `publish_skipped_not_head` (RR-DG10).

---

## Advice — recommended next wave (RR-W1)

| Priority | Track | Addresses | Approach sketch |
|----------|-------|-----------|-----------------|
| P0 | **Revision idempotency** | RR-DG3, RR-DG11 | Pre-check `_get_revision_for_head_sha`; IntegrityError recovery; optional row lock on `revision_count`; **no** `head_sha` unique index unless R0 decides migration |
| P0 | **Thread resolve diagnostics** | RR-DG1, RR-DG9 | Skip taxonomy in manifest; GraphQL error body; count `thread_id_not_found` separately |
| P1 | **Resolution stamp unblock** | RR-DG4 | Distinguish API compare_failed vs pairing vs line-region; extend `head_check_failed` / line-region HEAD verify |
| P1 | **Publish generation coherence** | RR-DG5, RR-DG10 | Treat SHA lag as blocked publish until R1 green; surface `publish_skipped_not_head` |
| P2 | **HEAD contradiction suppression** | RR-DG6 | Post-reconcile suppress when claim contradicted by file at `head_sha` (fixtures: matrix items 1–3, 15, 17) |
| P2 | **Inline 422 recovery** | RR-DG2 | Retry adjacent line or issue-comment fallback |

**Defer:** Re-litigating FR-CS4 Pass 3 supersede — orthogonal to this dogfood session.

---

## Decisions registry

| ID | Question | Status | Resolution |
|----|----------|--------|------------|
| **RR-Q1** | Is finding-resolution "done"? | **locked** | **Mechanisms shipped**; cross-repo operator gate **not** done |
| **RR-Q2** | Next pass scope? | **locked** | **RR-W1** — ingest + publish hygiene + HEAD truth (findings above) |
| **RR-Q3** | Use external repo for staging probes? | **locked** | TenderPro #130 validated for RR-W1; no dedicated probe repo required |
| **RR-Q4** | Block merge on 0% resolution rate? | **locked** | **Defer product gate until R5** — metric not trustworthy until R1–R3 green |
| **RR-Q5** | `head_sha` unique DB constraint? | **locked** | **(A) Application dedupe** — `_get_revision_for_head_sha` + `IntegrityError` recovery + optional `FOR UPDATE`; **no** Alembic unique on `(pull_request_id, head_sha)` unless R1.4 proves insufficient |

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
| RR-V1 | Rapid double-push → **one** revision row per `head_sha`; no IntegrityError; unit test for concurrent `_append_revision` |
| RR-V2 | After fix push, resolution rate **> 0%** on cohort with line edits — **requires R0 manifest** confirming stamp mechanism (not stale `compare_failed`) |
| RR-V3 | Successful publish: summary `head_sha` == revision `head_sha` == inline batch (cohort where R1 completes) |
| RR-V4 | Thread resolve: skip count **0** or manifest shows `thread_id_not_found` / `resolve_mutation_failed` breakdown — test on cohort where R3 stamps `addressed` |
| RR-V5 | Frozen checklist: operator matrix items **1, 2, 3, 15, 17** — **0/5** false positives published on re-run (`misc/SUPER_ADMIN_DASHBOARD_STAGING_VALIDATION.md`) |

---

## Peer review (2026-07-31) — incorporated

Architecture peer review against `main` **accepted** with tightenings above. **Valid:** R1 DB model detail, R2 skip taxonomy, R3 hypothesis split for RR-DG4, R4 suppression not new HEAD API, RR-DG9–11, RR-Q4 lock, RR-V5 fixtures. **Open for R0:** reconcile manifest / DB snapshot for the push that showed "Compare blocked: 6" (confirm `closure_blocked_reason` vs pairing); whether skipped threads were Revy-owned bot comments.

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
