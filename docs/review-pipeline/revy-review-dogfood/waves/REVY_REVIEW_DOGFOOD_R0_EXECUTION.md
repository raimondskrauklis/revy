# docs/review-pipeline/revy-review-dogfood/waves/REVY_REVIEW_DOGFOOD_R0_EXECUTION.md

# R0 — Baseline & prerequisites (execution)

Phase **R0** of [REVY_REVIEW_DOGFOOD_GENERAL_PLAN.md](../REVY_REVIEW_DOGFOOD_GENERAL_PLAN.md). Baseline: [REVY_REVIEW_DOGFOOD_FINDINGS.md](../REVY_REVIEW_DOGFOOD_FINDINGS.md) § Case study, RR-DG4. **R0 only.**

**Goal:** Lock RR-Q5, tag RR-DG4 root cause, and freeze RR-V1–V5 fixtures before any product code.

## Decisions locked for R0

- TenderPro #130 (`raimondskrauklis/tender_pro`, PR 130) is the primary evidence cohort; worker log `misc/tenderprolog.txt`, operator matrix `misc/SUPER_ADMIN_DASHBOARD_STAGING_VALIDATION.md`.
- RR-V5 checklist = operator matrix rows **1, 2, 3, 15, 17** with expected **suppress** on re-run after R4.
- RR-DG4 hypothesis must be **one primary tag** recorded in findings + validation memo § R0.2 before R3 starts: `api_compare_failed` | `pairing_gap` | `line_region_miss` | `stale_closure_blocked`.
- RR-Q4 locked: defer product merge gate until R5.
- No backend product code in R0.

## Out of scope for R0

- SSOT / Greptile / Bugbot → **R1.0**
- Revision idempotency code → **R1**
- Staging re-run PASS → **R5**

---

## R0.1 — Validation memo evidence import

**What:** Copy TenderPro session evidence into program validation memo: log event counts, cohort SHAs (`b4ba498`, `d915b4e`, `999ad17`), pass/fail table, dogfood push rows.

**Files:** `docs/review-pipeline/revy-review-dogfood/REVY_REVIEW_DOGFOOD_STAGING_VALIDATION.md`

**Deliverable:** Memo § Evidence sources + § Dogfood pushes filled; link to `misc/` paths for operator copies.

---

## R0.2 — RR-DG4 cohort diagnosis (staging DB or manifest)

**What:** For the publish that showed **Compare blocked: 6** / **0% resolution**, extract per active group: `closure_blocked_reason`, `resolution_status`, `last_seen_revision_id`, pairing revision set, whether compare API failed vs patch present for `file_path`.

**Files:** `docs/review-pipeline/revy-review-dogfood/REVY_REVIEW_DOGFOOD_FINDINGS.md` (§ RR-DG4 row + RC-3 tag), `REVY_REVIEW_DOGFOOD_STAGING_VALIDATION.md` (§ R0.2)

**Deliverable:** One paragraph **RR-DG4 primary tag** + evidence table (fingerprint, `closure_blocked_reason`, `last_seen_revision_id`, compare outcome). Run against staging DB (connection: [DATABASE_CONNECTION_GUIDE.md](../../../utils/DATABASE_CONNECTION_GUIDE.md)):

```sql
-- Replace :repo_full_name (e.g. 'raimondskrauklis/tender_pro'), :pr_number, :head_sha
SELECT g.fingerprint,
       g.state,
       g.closure_blocked_reason,
       g.resolution_status,
       g.file_path,
       g.last_seen_revision_id,
       r.revision_number AS last_seen_rev_num,
       r.head_sha AS last_seen_head_sha
FROM github_finding_groups g
JOIN github_pull_requests pr ON pr.id = g.pull_request_id
JOIN github_repositories repo ON repo.id = pr.repository_id
JOIN github_pull_request_revisions r ON r.id = g.last_seen_revision_id
WHERE repo.full_name = :repo_full_name
  AND pr.number = :pr_number
  AND g.state = 'active'
ORDER BY g.severity, g.title;

-- Latest reconcile resolution_pass manifest for revision at head_sha
SELECT rev.head_sha,
       rev.revision_number,
       a.content_json->'resolution_pass' AS resolution_pass
FROM github_pipeline_artifacts a
JOIN github_pipeline_steps s ON s.id = a.step_id
JOIN github_pipeline_runs pr ON pr.id = s.pipeline_run_id
JOIN github_review_runs rr ON rr.id = pr.review_run_id
JOIN github_pull_request_revisions rev ON rev.id = rr.revision_id
JOIN github_pull_requests gpr ON gpr.id = rev.pull_request_id
JOIN github_repositories repo ON repo.id = gpr.repository_id
WHERE repo.full_name = :repo_full_name
  AND gpr.number = :pr_number
  AND rev.head_sha = :head_sha
  AND s.step_type = 'reconcile'
  AND a.kind = 'manifest'
ORDER BY a.created_at DESC
LIMIT 1;
```

**Human gate:** If DB unavailable, operator pastes query output into validation memo § R0.2 — LOOP may proceed with tag `unknown_pending_db` only for R3.1 stale-clear work; **R3.2–R3.5 blocked** until primary tag locked.

---

## R0.3 — RR-Q5 decision (head_sha uniqueness)

**What:** Document locked choice: **(A)** application dedupe via `_get_revision_for_head_sha` + IntegrityError recovery only, or **(B)** hand-written migration adding unique `(pull_request_id, head_sha)` on `github_pull_request_revisions`.

**Files:** `REVY_REVIEW_DOGFOOD_FINDINGS.md` (decisions RR-Q5 → locked), `REVY_REVIEW_DOGFOOD_GENERAL_PLAN.md` (locked table)

**Deliverable:** RR-Q5 row status **locked** with A or B; if B, note migration filename placeholder for R1.

---

## R0.4 — RR-V fixtures & repro protocol

**What:** Add § RR-V gates to validation memo with explicit pass rules matching findings § Experiment / verification; document staging repro: (1) rapid double-push same SHA, (2) two **different** SHAs within 15s (TenderPro rev-13 scenario), (3) merge `origin/main` then fix-push.

**Files:** `REVY_REVIEW_DOGFOOD_STAGING_VALIDATION.md`

**Deliverable:** RR-V1–V5 table:

| Gate | Pass (findings authority) |
|------|---------------------------|
| RR-V1 | One revision row per `head_sha`; no IntegrityError; concurrent append unit test |
| RR-V2 | Resolution rate **> 0%** on fix-push cohort (after R3; manifest confirms stamp mechanism) |
| RR-V3 | Successful publish: summary `head_sha` == revision `head_sha` == inline batch |
| RR-V4 | Thread resolve skips **0** or manifest shows `thread_id_not_found` / `resolve_mutation_failed` breakdown |
| RR-V5 | Matrix items **1, 2, 3, 15, 17** — **0/5** false positives published |

---

## R0.5 — Thread ownership note (RR-DG1)

**What:** Operator confirms whether 18 skipped threads on TenderPro #130 rev 12 were **revybot-owned** inline comments (affects R2 `thread_not_revy_owned` counting). Record in validation memo § R0.5.

**Files:** `REVY_REVIEW_DOGFOOD_STAGING_VALIDATION.md`

**Deliverable:** One line: `thread_owner=revybot|mixed|unknown` with GitHub PR link to sample thread. If `unknown`, R2 ships counting-only (no ownership filter).

---

**Phase gate** (docs only):

```bash
rg 'RR-Q5.*locked|locked.*RR-Q5' docs/review-pipeline/revy-review-dogfood/REVY_REVIEW_DOGFOOD_FINDINGS.md
rg 'RR-DG4 primary tag|primary tag:' docs/review-pipeline/revy-review-dogfood/REVY_REVIEW_DOGFOOD_STAGING_VALIDATION.md
rg 'RR-V1' docs/review-pipeline/revy-review-dogfood/REVY_REVIEW_DOGFOOD_STAGING_VALIDATION.md
test -f docs/review-pipeline/revy-review-dogfood/REVY_REVIEW_DOGFOOD_STAGING_VALIDATION.md
```

**Human gate:** RR-DG4 primary tag locked in validation memo § R0.2 (or explicit `unknown_pending_db` scope documented).

**Next:** [REVY_REVIEW_DOGFOOD_R1_EXECUTION.md](./REVY_REVIEW_DOGFOOD_R1_EXECUTION.md)
