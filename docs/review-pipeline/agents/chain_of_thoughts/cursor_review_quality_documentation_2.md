# Review quality documentation
_Exported on 27/07/2026 at 14:07:12 EEST from Cursor (3.13.10)_

---

**User**

/architecture-peer-review 

docs/review-pipeline/review-quality/README.md

on all files in this folder

---

**Cursor**

I'll read the review-quality docs and cross-check their claims against the codebase.


Cross-checking the docs' claims against the codebase.


# Architecture peer review — `docs/review-pipeline/review-quality/`

Cross-checked all nine files against the backend (`github_indexing`, `github_review`, `github_finding_reconcile`, `github_publish`, `review_pipeline`, models, APIs) and reviewer frontend. **Verdict:** the baseline diagnosis is accurate and the slice structure is sound, but there are a few **dependency errors** and **underspecified migrations** that would cause rework if execution starts without fixing them.

---

## What the docs get right (verified)

| Claim | Code evidence |
|-------|----------------|
| Full-repo tarball index, no diff/compare | `run_index_job` iterates all `iter_indexable_files` after tarball extract |
| Review = global RAG, no unified diff | `_build_review_prompt` = title + chunk bodies only |
| 3 lenses × top 10, cap 30 | `SEARCH_LENSES`, `TOP_K_PER_QUERY`, `CONTEXT_CHUNK_CAP` |
| Judge = text metadata only | `_build_judge_prompt` — no snippet |
| Publish = table summary, same body for check + comment | `build_summary_markdown` → both `update_check_run` and `create_issue_comment` |
| Fingerprint includes message → smoke #44 dupes | `compute_fingerprint(..., message=...)` — matches staging doc |
| No `base_sha`, no `index_mode`, no pipeline tables | `GitHubPullRequestRevisionORM` has only `head_sha`; webhook stores `base_ref` not `base.sha` |
| No `content_hash`, no `evidence_snippet`, no `resolution_status` | Models confirmed |
| Autostart wiring exists (R8) | `github_tasks.py` → `maybe_enqueue_pipeline_for_revision(..., autostart)`; migration `0017`; UI on `ReviewSettingsPage` |
| `items_view` is the right read permission | Pattern in `installation_review.py` |
| R8 prerequisite met on `main` | PR [#31](https://github.com/raimondskrauklis/revy/pull/31) merged 2026-07-26 |

The “what exists today” section in `REVIEW_QUALITY_FINDINGS.md` is a faithful picture of the codebase.

---

## Critical gaps (fix before execution)

### 1. R5 metrics depends on R7 dismiss/ack — **not shipped**

`REVIEW_QUALITY_R5_RESOLUTION_METRICS_GENERAL_PLAN.md` and findings **M1** assume:

> `dismissed` ← R7 dismiss; inputs include “R7 dismiss/ack UI state”

**Reality:** R7 execution explicitly deferred dismiss/ack (`REVIEW_PIPELINE_R7_EXECUTION.md` § out of scope). There is **no** dismiss/ack API (`grep` over `backend/app/api`), and **no** reviewer UI for it. `REVIEW_PIPELINE_PRODUCT_PATTERNS.md` marking dismiss as “shipped (UI)” is wrong.

**Impact:** G9 prose (“N issues fixed since last push”) cannot use human dismiss without new work. v1 can still ship with `addressed` / `still_open` heuristics + judge `resolved`, but the plan must either:
- add a small dismiss API + UI slice to review-quality, or
- decouple M1 v1 from human dismiss and document that `dismissed` = judge-only for now.

### 2. D10 fingerprint shape is underspecified vs schema

**Locked D10:** `title + file_path + start_line + category` (message excluded).

**Today:** `workspace_id + pull_request_id + file_path + category + normalized_message`.

**Gaps:**
- `github_finding_groups` has **no** `start_line`; fingerprint is group-level but line lives on `github_findings`.
- Changing fingerprint ingredients **orphans existing groups** on open PRs — no backfill/migration strategy in any doc.
- D10 omits `workspace_id` / `pull_request_id` (probably still required for uniqueness).

Lock the canonical inputs in execution, including how line-less findings fingerprint.

### 3. D8 `base_sha` — webhook already has it, ingestion drops it

`_extract_pr_fields` reads `base.sha` but only persists `base_ref`. D13 compare needs `base_sha` at revision create (D8). Without it, compare on re-push when base branch moves is ambiguous.

### 4. AS2 autostart — code vs staging verification

R8 autostart is **implemented** with unit tests (`test_github_tasks_autostart.py`, `test_review_pipeline.py`). AS2 reads like a code bug; it may be **staging ops verification** (migrations `0017`–`0018`, worker queues, toggle). Smoke #44 doc never exercised autostart.

**Recommendation:** reword AS2 as “staging e2e gate” and separate from feature work unless a specific bug is identified.

### 5. Compare fallback → `full` undermines diff-first on failure

Locked D13 fallback is sensible for reliability, but on a 1-line PR a compare 404/rate-limit silently reverts to the smoke #44 haystack unless `fallback_reason` is loud in **publish** (not just manifest). Execution should treat fallback as a **degraded** run (footer warning + maybe skip autostart on huge repos).

### 6. O8 retention purge — no Celery beat today

No `beat`, `purge`, or `retention` in backend workers. O8 needs infra choice (Celery beat schedule vs existing maintenance task pattern) — not just a migration.

### 7. O4 workspace retention override — no config surface

“90d default; workspace override” is locked, but `workspaces` has no retention column and no admin API for it. Either add schema + PATCH in R1, or defer override to v1.1 and document default-only.

---

## Inconsistencies / corners cut

| Topic | Issue |
|-------|--------|
| **Naming** | Review-pipeline R5 (reconcile/judge) vs review-quality R5 (metrics) — acknowledged in R4, but easy to confuse in execution/commits; use distinct prefixes in code (`resolution_status` vs reconcile service). |
| **R6-Q2 vs G2** | R6 shipped severity-only check conclusion; G2 adds 0–5 confidence in narrative. Fine if confidence is **comment-only**, but execution must not break `compute_check_conclusion`. |
| **G3 split bodies** | Today one `build_summary_markdown` for both surfaces — G3 is net-new (`build_pr_review_comment` doesn’t exist). |
| **G8 `summary_json`** | Not on `github_publish_jobs` — needs migration in R3. |
| **Admin `POST …/index?mode=full`** | D2 mentions query param; `installation_indexing.py` has no `mode` — add to R1 or drop from API contract. |
| **R1 scope** | D13 + O tables + API + purge + D10 + SC3 + AS2 in one slice is large; execution file should split 5–6 subphases with a hard migration subphase 0. |
| **R3 ↔ R5 ordering** | R3 depends on R5 `resolution_status`; R5 depends on R3 snapshots. Same PR is fine, but execution must order: snapshot column → resolution job on `synchronize` → formatter hook. |
| **Parent program docs stale** | `REVIEW_PIPELINE_RECOVERY_CHECKLIST.md` still says “merge R8”; R8 is merged. Review-quality README is correct on prerequisite. |
| **Findings M track** | Says “after dismiss flows have production data” but registry M1 is locked — contradicts R5’s R7 dependency. |

---

## Per-slice notes

### README + `REVIEW_QUALITY_GENERAL_PLAN.md`
Solid index. `waves/REVIEW_QUALITY_EXECUTION.md` correctly marked “next.” One PR / one migration chain is realistic if execution subphases are strict.

### `REVIEW_QUALITY_FINDINGS.md`
Strong baseline. Minor fixes:
- Autostart table: backend gate is `review_pipeline.py`, not only `github_tasks.py`.
- Track M phasing vs locked M1 (see above).
- Edge case “judge all fail → `judge_status=completed`” — verify polish J5 behavior in code during execution (not re-checked here).

### `REVIEW_QUALITY_R1` (D + O)
Highest-risk slice. D13 hybrid (compare list + tarball bytes for changed paths only) fits existing `download_repository_tarball` + `chunk_file_content`. New work: `github_api.compare_commits`, revision `base_sha`, scoped retrieval, context pack rewrite, three pipeline tables, `GET …/pipeline`, purge job, D10 reconcile change, SC3 manifest fields.

**SC3 in R1 is right** — cheap instrumentation for structural gap.

### `REVIEW_QUALITY_R2` (C1)
Depends on parent revision resolution (revision_number − 1) and D8 compare paths. Copy-forward + `content_hash` on `github_code_chunks` is clean. **First push** has no parent — docs should state explicit no-op. Delete-removed-paths step needs compare against **parent revision’s base/head**, not just file list diff.

### `REVIEW_QUALITY_R3` (G)
Greptile formatter + publisher LLM is the largest **product** unknown (latency, cost, failure fallback to table). Fallback to R6 table is locked — good. Idempotency per `head_sha` already exists via `find_publish_job_for_head_sha`.

### `REVIEW_QUALITY_R4` (E)
Depends on review-pipeline R5 reconcile — **exists**. Evidence from diff hunk requires R1 diff in context pack at parse time. Judge `dismissed` → `resolved` already exists; grounding is additive. Clarify whether dismissed-by-grounding sets `resolved` or a new state.

### `REVIEW_QUALITY_R5` (M + G9)
**Blocked on dismiss** unless scoped down. Diff heuristic for `addressed` needs `start_line`/`end_line` on groups or join to latest finding — not specified. `resolution_status` is new enum column on `github_finding_groups` — not in findings registry table section (add to migration list).

### `REVIEW_QUALITY_STRUCTURAL_CONTEXT.md`
Best doc in the folder. Honest v1 positioning, SC8 north star, Path C for v1.1 is proportional. No code conflicts; SC3 fields are the only v1 touchpoint.

---

## Execution-planning checklist

Before `create-execution-plan`:

1. **Resolve R5 / dismiss** — ship without human dismiss, or add minimal dismiss API + reviewer action.
2. **Lock D10 migration** — fingerprint formula + existing open PR behavior.
3. **Lock D8** — `base_sha` on `github_pull_request_revisions` (or PR + revision), populated from webhook `base.sha`.
4. **Clarify AS2** — verification gate vs code fix.
5. **O8/O4** — default-only 90d purge first; workspace override later if needed.
6. **Subphase R1** — migration 0: `base_sha`, `index_mode`, pipeline tables, `content_hash` (if R2 same chain), `resolution_status`, `summary_json`, `evidence_snippet` in one chain or explicitly ordered.
7. **Phase gate S4** — add autostart path to smoke checklist (not only #44 replay via command).

---

## Questions (scope only)

1. **AS2:** Is autostart still failing on staging after R8/#31, or is AS2 purely “re-run staging e2e with toggle on”?
2. **R5 v1:** Should human dismiss be **in** review-quality-v1, or should M1 v1 use judge-resolved + diff heuristic only (defer dismiss to a small follow-up)?
3. **D10:** On fingerprint change, OK to **reset** group linkage for in-flight open PRs, or require backfill?

---

**Bottom line:** Ship the program, but don’t start `phase-execution` until R5’s R7 dismiss dependency and D10/D8 migration details are resolved in the execution plan. The diff-first + trace foundation (R1) is the right priority; structural context deferral (SC1) is justified. The biggest product risk is R3 (Greptile LLM formatter + G3 split), not R1 indexing.

---

**User**

agent updated general plans and cretaed execuytion plans

please review

/execution-peer-review  on REVIEW_QUALITY_EXECUTION.md

---

**Cursor**

Reviewing `REVIEW_QUALITY_EXECUTION.md` against the general plans, findings, and codebase — starting with the execution table and that file.


Cross-checking the execution file against the general plans, findings, and cited codebase paths.


**Plan:** `docs/review-pipeline/review-quality/` · **Execution file:** `waves/REVIEW_QUALITY_EXECUTION.md` (single file)  
**LOOP order:** RQ0 → RQ1 → RQ2 → RQ3 → RQ4 → RQ5 → RQ6 → RQ7 → RQ8 (9 sections — one over the 3–8 subphase guideline)

Peer-review resolutions (M2, D10, D13-F, O4-v1) are incorporated in the header. Below is per-section review against general plans, findings, and repo.

---

## RQ0 — `waves/REVIEW_QUALITY_EXECUTION.md` (schema)

| Severity | Area | Finding |
|:---|:---|:---|
| high | findings | `github_pipeline_runs` columns from findings (`index_job_id`, `review_run_id`, `publish_job_id`, `revision_id`, `head_sha`, `index_mode`) are **not listed** in RQ0 — implementer must infer from findings § storage model. |
| medium | execution | No `fallback_reason` / warning column on `github_index_jobs` — RQ1 requires `fallback_reason` on job metadata; only `index_mode` is in migration table. |
| medium | execution | RQ2 says “persist raw LLM response on review run” but RQ0 adds **no** `raw_response` column on `github_review_runs`; O2 expects pipeline artifacts — RQ2/RQ3 should say pipeline-only, not review_run column. |
| low | codebase | `tests/unit/test_migrations.py` **does not exist**; deliverable fallback (“import models smoke”) is weak — name a concrete test file to add or use existing model import path. |

**Verified OK:** Hand-written `0026` after `0025` (`2026_07_27_0000_0025_*`); LOOP pause for human migration; enums called out; D10-M / M2 locked in header.

---

## RQ1 — Compare API + base_sha + diff index

| Severity | Area | Finding |
|:---|:---|:---|
| critical | execution | **Index mode timing:** “resolve `index_mode` from review profile” in `run_index_job` is wrong — review run does not exist when index runs (`index_tasks.py` → `prepare_review_after_index` → then `create_review_run`). For autostart/command, set `index_mode=diff` on **job create** in `maybe_enqueue_pipeline_for_revision` / `GitHubIndexJobORM`; map `deep`/`critical` only when review is triggered with that profile (admin API path). |
| high | codebase | Pipeline API path in RQ3 uses `…/installations/{id}/repositories/…` — **wrong**. Existing routes use `…/workspaces/{workspace_id}/repositories/{repository_id}/…` (`installation_review.py` has no `installations` segment). |
| medium | general plan | R1 general plan allows optional `POST …/index` body for `mode=full`; RQ1 omits admin index mode — manual index stays full-repo-only unless added. |
| medium | findings | D3 wants `full` warning in **job metadata + GitHub footer**; RQ1 only covers job warning; footer deferred to RQ7 — OK if intentional, but D3 “typical duration” estimate not specified in RQ1. |
| low | clarity | `review_pipeline.py` listed but only needs `index_mode` on job create, not profile resolution at index run time. |

**Verified OK:** `compare_commits` net-new in `github_api.py` (verified absent); `_extract_pr_fields` / `base_sha` gap confirmed; `test_github_api.py` exists; D13 hybrid matches `run_index_job` + tarball flow.

---

## RQ2 — Diff-first review + retrieval + fingerprint

| Severity | Area | Finding |
|:---|:---|:---|
| high | execution | Item 5: “persist raw LLM response on review run” + `parse_report` **artifact** before RQ3 creates `github_pipeline_trace.py` — either move storage to RQ3 or add interim columns in RQ0. Findings O2/O1 are pipeline artifacts, not review_run fields. |
| medium | findings | O6 (“prefer chunk refs + assembled prompt”) not mentioned — risk of triple-storing chunk text in prompt artifacts. |
| medium | findings | D5 edge case: `truncated=true` + omitted hunks in manifest when diff capped — not in RQ2. |
| low | execution | `parse_report` with `dropped_count`/reasons — `_parse_finding_row` drops style silently today; no drop audit spec (counts only vs reasons). |

**Verified OK:** D10 formula matches peer-review lock; `compute_fingerprint` in `github_finding_reconcile.py` verified; SC3 fields listed; D6/D7/D12 aligned with findings; tests paths exist.

---

## RQ3 — Pipeline trace + read API + purge

| Severity | Area | Finding |
|:---|:---|:---|
| critical | execution | **Wire capture incomplete in Files list** — must include worker entrypoints: `index_tasks.py`, `review_tasks.py`, `reconcile_tasks.py`, `publish_tasks.py` (judge runs inline in reconcile per `reconcile_tasks.py`). Without these, steps won’t be recorded end-to-end. |
| high | execution | Pipeline **GET route** must follow existing pattern, e.g. `GET /workspaces/{workspace_id}/repositories/{repository_id}/pull-requests/{pull_request_id}/review-runs/{run_id}/pipeline` (or revision-scoped variant) — not the `installations/…` path in RQ3. |
| high | codebase | `maintenance_tasks.py` is routed in `celery_app.py` but **file does not exist**; O8 “beat or maintenance” is an open fork — pick one in RQ3 and register the module in `celery_app` imports (maintenance not imported today). |
| medium | findings | O9 `admin_users` retention/export API — not in execution (may be intentional with O4-v1; general plan still mentions admin export). |
| medium | execution contract | O8 infra choice (“Celery beat **or** maintenance task”) = unresolved “choose A or B” per skill checklist. |
| low | execution | `reconcile` step capture — listed in step types but no explicit hook in `github_finding_reconcile.py` / `reconcile_tasks.py` in Files. |

**Verified OK:** `items_view` permission pattern verified; `installation_review.py` is correct mount point for new route; O1–O3/O7 artifact kinds align with findings; purge `PIPELINE_RETENTION_DAYS` + `.env.example` in RQ8.

---

## RQ4 — Incremental copy-forward (C1)

| Severity | Area | Finding |
|:---|:---|:---|
| medium | general plan | R2 general plan **I3** (`incremental` vs `full` re-embed flag on index job) missing from RQ4 — only `content_hash` + copy-forward covered. |
| low | execution | Depends on RQ1 compare + RQ3 index manifest — order OK (RQ4 after RQ1; manifest fields need RQ3 service or inline manifest in indexing until wired). |

**Verified OK:** First-push no-op documented in general plan; parent revision by PR; delete removed paths; test filter `-k incremental` is concrete.

---

## RQ5 — Evidence + grounding judge (E)

| Severity | Area | Finding |
|:---|:---|:---|
| low | execution | Hard gate “RQ2 before RQ5 (diff in context before evidence from hunk)” — satisfied if LOOP order kept. |
| low | clarity | “Judge dismissed → existing `resolved`” — matches `github_finding_judge.py` behavior; no new enum — good. |

**Verified OK:** `evidence_snippet` in RQ0; `_build_judge_prompt` in `github_finding_judge.py` verified text-only; test files exist.

---

## RQ6 — Resolution metrics (M2, G8)

| Severity | Area | Finding |
|:---|:---|:---|
| medium | general plan | R5 general plan says depends on R3 `summary_json`; RQ6 does not reference it — **OK for M2** (heuristic does not need snapshot), but G9 “prior delta” in RQ7 may need `summary_json` from **prior publish**, not resolution job. |
| medium | execution | Hook “revision ingest or Celery after compare” — should name **where** in `apply_pull_request_webhook_event` / `_append_revision` vs post-index, so resolution runs **before** RQ7 publish on second push. Hard gate RQ6→RQ7 is correct. |
| low | findings | M2 enum `judge_dismissed` vs findings registry still saying `dismissed` in some tables — execution uses M2 names consistently. |

**Verified OK:** M2 scoped without human dismiss; unit test cases match peer-review; `resolution_status` in RQ0 schema.

---

## RQ7 — Greptile publish (G, G3, G9, D13-F)

| Severity | Area | Finding |
|:---|:---|:---|
| medium | execution | G5 **publisher LLM** — no integration file named (only `integrations/*` if separate); add concrete module (`moonshot_review` extension vs new formatter client) to avoid spike mid-LOOP. |
| medium | findings | G6 P2 inline off / G7 message column off — not repeated in RQ7 (inherited from R6; should assert no regression in deliverable). |
| low | execution | D3 full-mode duration warning in GitHub footer — only D13-F fallback called out; explicit D3 `full` warning on deep/critical path could be missing if index was intentionally `full`. |

**Verified OK:** G3 split, G2 vs R6-Q2, G9 from `resolution_status`, G8 `summary_json`, D13-F footer; `build_summary_markdown` verified as today’s fallback; hard gate after RQ6.

---

## RQ8 — Doc sync + staging gates

| Severity | Area | Finding |
|:---|:---|:---|
| low | execution contract | Doc-sync subphase present; human gate S4 + AS2 checklist is strong; final `pytest tests/unit/` gate is comprehensive. |
| low | clarity | No `post-finish-gap-pass` mention — optional per skill for final phase. |

**Verified OK:** Phase gate lists all new test modules; human gate covers smoke #44, D10, G3, pipeline API, AS2; tag `review-quality-v1` stated.

---

## Rollup

```
Review complete: 1 file (9 LOOP sections), 2 critical, 5 high, 12 medium, 8 low.
BLOCK phase-execution: no — proceed with fixes below (can implement around critical items if execution agent follows peer-review locks).
```

### Critical / high (fix or explicitly accept in execution file)

1. **Index `index_mode` at job creation**, not from review profile inside `run_index_job`.
2. **Pipeline API path** — drop `installations/{id}`; align with `installation_review.py` route shape.
3. **Raw LLM storage** — pipeline artifacts only (RQ2 wording + RQ3 workers in Files).
4. **RQ0** — add `github_pipeline_runs` FK columns + `fallback_reason` (or document manifest-only) on index job.
5. **RQ3** — list all worker hooks; **resolve O8** (create `maintenance_tasks.py` or Celery beat + import).

### Safe to start?

**Yes**, with the above understood. The plan correctly absorbs architecture peer-review (M2, D10-M, D13-F, O4-v1, AS2 as staging gate). Biggest implementation risks: RQ1 index/review ordering, RQ3 end-to-end trace wiring, RQ7 formatter LLM spike.

### Blocking questions (max 2)

1. **Pipeline route:** Confirm `…/repositories/{repository_id}/pull-requests/{pull_request_id}/review-runs/{run_id}/pipeline` vs revision-nested `…/revisions/{revision_id}/review-run/{run_id}/pipeline` to match existing `review-run` (singular) pattern?
2. **O8:** Prefer new `pipeline_purge_tasks.py` on `maintenance` queue (matches `export_tasks`) over Celery beat for v1?

---

**User**

agent modified. make one more pass

The execution peer review is accurate — I re-verified against installation_review.py, index_tasks.py → prepare_review_after_index, and celery_app.py (routes maintenance_tasks.* but file missing).

Verdict
Proceed to phase-execution — all critical/high items are incorporated in REVIEW_QUALITY_EXECUTION.md.

Critical fixes applied
Finding	Fix
index_mode from review profile in run_index_job
Set on GitHubIndexJobORM at create: autostart/command → diff; manual index → full (+ optional body mode)
Wrong pipeline API path
GET …/repositories/{repository_id}/pull-requests/{pull_request_id}/revisions/{revision_id}/review-runs/{review_run_id}/pipeline — no installations/ segment
Raw LLM on review_run
O2 pipeline artifacts only — RQ2 builds parse_report dict; RQ3 persists prompt/raw_response
Incomplete RQ0
Full github_pipeline_runs FK columns + fallback_reason + index_incremental on index jobs
Missing worker hooks
RQ3 lists index_tasks, review_tasks, reconcile_tasks, publish_tasks, judge path
Blocking questions — locked
Pipeline route: Revision-scoped plural review-runs/{review_run_id}/pipeline — matches existing installation_review.py pattern (review-run singular for latest GET; plural for specific run + trace).

O8: pipeline_purge_tasks.py on maintenance queue + one beat_schedule entry in celery_app.py — not the nonexistent maintenance_tasks.py.

Other incorporations
D5 truncated + omitted_files[] in RQ2
O6 chunk refs in RQ3
I3 index_incremental in RQ0/RQ4
RQ6 hook: after revision create, before pipeline enqueue
G5: github_publish_formatter.py + Moonshot pattern (concrete module)
G6/G7 regression assertions in RQ7
D3 footer deferred to RQ7 (intentional split with job warning in RQ1)
Deliverable: test_review_quality_models.py instead of missing test_migrations.py
Execution peer-review table appended at bottom of execution file
9 LOOP sections is one over the 3–8 guideline but acceptable for a single-PR mega-phase — subphases are now tight enough to implement.

---

**Cursor**

Re-reading the updated execution file and verifying the claimed fixes against the codebase.


**Plan:** `review-quality/` · **File:** `waves/REVIEW_QUALITY_EXECUTION.md` (single file, RQ0–RQ8)  
**Re-verified:** `installation_review.py`, `review_pipeline.py`, `index_tasks.py`, `celery_app.py`, migration chain (`0025` → `0026`)

Previous critical/high items are incorporated. Second pass below — mostly clean, a few **medium** gaps left (none blocking).

---

## RQ0 — Schema migration

| Severity | Area | Finding |
|:---|:---|:---|
| medium | execution | RQ1 item 6 sets `warning_message` on index job, but RQ0 **`github_index_jobs` table omits `warning_message`** — add column in `0026` or drop job-level D3 text and rely on pipeline manifest only. |
| low | findings | Workspace-delete cascade on `github_pipeline_*` (compliance in findings) not mentioned — rely on FK `ON DELETE CASCADE` from `workspace_id` or document as follow-up. |

**Verified OK:** Full `github_pipeline_runs` FK set; `fallback_reason` + `index_incremental`; no `raw_response` on review runs; `test_review_quality_models.py` named; `0026` chains after `0025`.

---

## RQ1 — Compare + diff index

| Severity | Area | Finding |
|:---|:---|:---|
| medium | execution | AS1 lock (line 12): admin `POST …/review` with `deep`/`critical` → new `index_mode=full` job or reject mismatch — **not in RQ1 Files** (`installation_review.py`, `create_review_run` guard missing). Easy to miss during LOOP. |
| medium | execution | **Compare handoff RQ1→RQ2:** index uses compare for `changed_files`; RQ2 needs unified diff — execution doesn’t say **re-call `compare_commits` in review** vs cache patches on index job. Recommend one line: “review loads latest completed index job + re-calls compare (or reads `changed_files` from index step artifact once RQ3 lands).” |
| low | clarity | “file manifest on job metadata (until RQ3)” — no JSON column listed in RQ0; use pipeline artifact after RQ3 or add `index_manifest_json` if needed pre-RQ3. |

**Verified OK:** `index_mode` at job create (not `run_index_job` profile); `maybe_enqueue_pipeline_for_revision` is the right hook; `installation_indexing.py` optional `mode`; route pattern matches workspace router.

---

## RQ2 — Diff-first review + fingerprint

**RQ2 — no gaps found.**

**Verified OK:** O2 deferred to RQ3 explicit in hard gates; D5 `truncated`/`omitted_files[]`; D10 formula; `parse_report` dict only until RQ3 persists.

---

## RQ3 — Pipeline trace + API + purge

| Severity | Area | Finding |
|:---|:---|:---|
| medium | ops | O8 adds **`beat_schedule`** — first beat usage in repo (`celery_app.py` has no beat today). RQ8 human gate should add: “Celery beat process running on staging” or purge won’t run. |
| low | execution | `retrieve` as separate `step_type` — retrieval still lives inside `github_review.py`; execution should record retrieve as its own step before review (or document as sub-step of review). |

**Verified OK:** All worker modules listed; pipeline GET path matches `installation_review.py` (`review-run` singular for latest GET; plural `review-runs/{id}/pipeline` for trace is consistent); `pipeline_purge_tasks.py` + maintenance queue; O6 chunk refs called out.

---

## RQ4 — Incremental copy-forward

**RQ4 — no gaps found.**

**Verified OK:** I3 `index_incremental`; first-push no-op; manifest via RQ3 index step; runs after RQ3 in LOOP order.

---

## RQ5 — Evidence + judge

**RQ5 — no gaps found.**

**Verified OK:** Depends on RQ2 diff + RQ3 judge hooks; `evidence_snippet` in RQ0.

---

## RQ6 — Resolution metrics

| Severity | Area | Finding |
|:---|:---|:---|
| low | execution | RQ6 runs compare **before** pipeline enqueue; index + review will call compare again on same push — acceptable, but 2–3 compare calls per `synchronize` is worth noting for rate limits (not a plan bug). |

**Verified OK:** Hook placement (`_append_revision` before `maybe_enqueue_pipeline_for_revision`); M2 without human dismiss; G8 delta correctly scoped to RQ7.

---

## RQ7 — Greptile publish

**RQ7 — no gaps found.**

**Verified OK:** `github_publish_formatter.py` + Moonshot; G3/G2/G6/G7; D3 + D13-F footer; G9 from RQ6; hard gate after RQ6.

---

## RQ8 — Doc sync + staging gates

| Severity | Area | Finding |
|:---|:---|:---|
| medium | execution contract | Body trimmed to “Doc table per prior RQ8” — **less explicit** than before (no file list in this revision). Implementer should still update the five docs named in the first-pass version; consider restoring the table for phase-execution agents. |
| low | execution | `post-finish-gap-pass` marked optional — fine. |

**Verified OK:** Full phase gate includes all new test modules; human gate covers S4 + AS2 + D10 + G3 + pipeline GET.

---

## Rollup

```
Review complete: 1 file (9 LOOP sections), 0 critical, 0 high, 5 medium, 5 low.
BLOCK phase-execution: no.
```

### Prior critical/high — confirmed fixed

| # | Topic | Status |
|---|--------|--------|
| 1 | `index_mode` at job create | Locked + RQ1 aligned |
| 2 | Pipeline API path | Matches `installation_review.py` |
| 3 | O2 pipeline-only raw capture | RQ2/RQ3 split clear |
| 4 | RQ0 schema completeness | FKs + `fallback_reason` + `index_incremental` |
| 5 | Worker hooks | All task modules in RQ3 |
| 6 | O8 | `pipeline_purge_tasks.py` + beat (not `maintenance_tasks.py`) |

### Optional doc tweaks (non-blocking)

1. Add `warning_message` to RQ0 `github_index_jobs` row.  
2. Add `installation_review.py` to RQ1 Files for deep/critical re-index guard.  
3. One line on compare reuse in RQ2.  
4. Restore RQ8 doc file table.  
5. Human gate: Celery beat running for O8.

**Verdict:** Agree with your assessment — **proceed to `phase-execution` on `feat/review-quality` starting at RQ0.** Remaining items are implementer notes, not plan defects.

---

**User**

update all docs needed

---

**Cursor**

I'll read the current docs and apply the peer-review fixes across the execution file and any related docs that need syncing.


Updating the execution file and syncing related docs from the peer-review passes.


Updated docs from both execution peer-review passes. Summary:

### Primary — `waves/REVIEW_QUALITY_EXECUTION.md`
- RQ0: `warning_message` on `github_index_jobs`; `workspace_id` FK with `ON DELETE CASCADE` on `github_pipeline_runs`
- RQ1: AS1 deep/critical path via `installation_review.py` + `create_review_run`; clarified index manifest → pipeline (no extra job JSON)
- RQ2: compare handoff — re-call `compare_commits` in review worker
- RQ3: explicit `retrieve` step_type
- RQ8: restored doc sync table; Celery **beat** in human gate + deploy note
- Execution peer-review section: pass 1 + pass 2 table (items 11–17)

### Review quality program
- `review-quality/README.md` — AS2 wording; status → execution peer-reviewed
- `REVIEW_QUALITY_FINDINGS.md` — AS2 staging gate; next → `phase-execution`
- `REVIEW_QUALITY_GENERAL_PLAN.md` — AS2 prerequisite; next step
- `REVIEW_QUALITY_PEER_REVIEW.md` — execution peer-review section; checklist complete
- `REVIEW_QUALITY_R1_DIFF_AND_TRACE_GENERAL_PLAN.md` — AS2 staging gate wording

### Parent program
- `REVIEW_PIPELINE_RECOVERY_CHECKLIST.md` — R8 merged; **Track H** review-quality; snapshot refreshed; parking lot + agent resume
- `REVIEW_PIPELINE_GENERAL_PLAN.md` — R8 shipped; next → review-quality
- `REVIEW_PIPELINE_README.md` — next order; R8 on `main`
- `REVIEW_PIPELINE_R8_AUTOMATION_GENERAL_PLAN.md` — shipped pointer
- `REVIEW_PIPELINE_PRODUCT_PATTERNS.md` — precision metrics → review-quality M2 (in flight)
- `waves/README.md` — execution peer-reviewed status

Ready for **`phase-execution` on `feat/review-quality` starting at RQ0**.

---

**User**

/phase-execution 

implement 0 phase only, than run local bugbot an then push to fresh branch. we will have greptile runng in paralell. so we can adjust as we go. grpetile approachis very good, so we can distile something

don't know do we have this in plan - i always tray ship md plang docs in same pr as code (stepb by step phases) and i have feeling that greptile/bugbot uses them and review is better since there is much more context

---

**Cursor**

Implementing RQ0 only: checking the branch and codebase, then building the migration and models.


---

**User**

actualy check this md apprach first. we ave now many md files and will have code for phasees. do we pass also md files as diff?

---

**Cursor**

Checking how Greptile/Bugbot use PR diffs and whether planning docs in the same PR feed their review context.


Your instinct is directionally right, but the mechanics differ between **Greptile**, **Bugbot**, and what actually helps review quality.

## Short answer

**Yes — changed `.md` files are in the PR diff** and both tools can see them.  
**No — they do not automatically treat every planning doc as authoritative spec context** just because it’s in the repo or in the PR.

Docs help most when they are either:
1. **in the diff** (changed this push), or  
2. **explicitly wired** as review context (Greptile `files.json` / Bugbot `BUGBOT.md` links).

---

## What each tool actually reads

### Greptile

| Source | Included? |
|--------|-----------|
| **PR diff** (all changed files, including `docs/**/*.md`) | Yes — part of the review |
| **Pre-indexed repo graph** | Yes — main cross-file context (callers, patterns) |
| **Planning docs as “spec”** | Only if configured via `.greptile/files.json` or `greptile.json` `customContext.files` |

Greptile’s docs describe `files.json` as pointing the reviewer at architecture/plan files **in the repo**, with optional `scope` globs (e.g. only when reviewing `backend/**`). That is separate from “this file happened to change in the PR.”

Your own learnings doc already notes Greptile catching **“doc drift in same PR”** — so changed planning docs *are* read to some degree, but mostly for consistency/narrative, not as a full execution contract unless you wire them.

### Bugbot (Cursor)

| Source | Included? |
|--------|-----------|
| **Full PR diff** (`base…head`) | Yes — default |
| **`.cursor/BUGBOT.md`** | Yes — hierarchical from changed paths |
| **Other `.md` via links in `BUGBOT.md`** | Yes — Bugbot follows relative `[links](path.md)` |
| **All repo docs automatically** | No |
| **`.cursor/rules/`** | No — IDE agent only |

Important caveat from Cursor’s forum: on large PRs there is a **context budget**. Summary processing can be path-order sensitive; lots of dotfiles/config/lockfiles/docs early in the alphabet can consume budget before your core code. Bug detection handles large diffs differently, but **doc-heavy PRs can still dilute attention**.

### Local `/review-bugbot` (pre-push)

Reviews **branch diff vs base** (committed + uncommitted). Same rule: changed MD is in the patch. It does not magically load the whole `docs/review-pipeline/` tree unless linked or changed.

---

## Your “MD + code in same PR, phase by phase” approach

**This is a good workflow** and matches what worked on [#35](https://github.com/raimondskrauklis/revy/pull/35) (Greptile narrative bullets by subsystem). It is **not fully spelled out** in `REVIEW_QUALITY_EXECUTION.md`, but it aligns with:

- **S1** — one PR for the program  
- **RQ8** — doc sync at the end  
- Historical pattern — polish/R-stack PRs updated docs alongside code  

What’s missing is an explicit **“review context”** step — how bots should consume the plans.

### What works well

- Commit **RQ0 code + execution status update** together (“RQ0 done” in `waves/README.md`)
- Keep **locked decisions in the execution header** (you already do — high signal per push)
- Small, phase-scoped doc edits beat re-touching 15 files every commit

### What does *not* happen automatically

- Greptile does not read `REVIEW_QUALITY_FINDINGS.md` (520 lines) as binding spec for every `backend/` hunk unless in diff or `files.json`
- Bugbot does not ingest the whole `review-quality/` folder unless linked from `BUGBOT.md` or changed

---

## Practical recommendation (before RQ0)

If you want bots to use plans as context **reliably**, add lightweight wiring (optional, ~10 lines):

**Greptile** — `.greptile/files.json`:

```json
{
  "files": [
    {
      "path": "docs/review-pipeline/waves/REVIEW_QUALITY_EXECUTION.md",
      "description": "Active execution contract — locked decisions, RQ scope",
      "scope": ["backend/**"]
    },
    {
      "path": "docs/review-pipeline/review-quality/REVIEW_QUALITY_FINDINGS.md",
      "description": "Locked Q# registry",
      "scope": ["backend/**"]
    }
  ]
}
```

**Bugbot** — `.cursor/BUGBOT.md`:

```markdown
## Review quality (feat/review-quality)

When reviewing backend pipeline changes, also read:
- [Execution (RQ0–RQ8)](../docs/review-pipeline/waves/REVIEW_QUALITY_EXECUTION.md)
- [Locked findings](../docs/review-pipeline/review-quality/REVIEW_QUALITY_FINDINGS.md)
```

Ship those in the **first** review-quality commit with RQ0 — then every subsequent phase push inherits the context without re-explaining.

---

## Suggested commit pattern per phase

| Commit | Include |
|--------|---------|
| `feat(review-quality): RQ0 schema migration` | `0026` + models + `test_review_quality_models.py` + `.greptile/files.json` / `BUGBOT.md` (if you add them) + `waves/README.md` status → RQ0 done |
| Later RQn | Code for slice + one-line execution progress + only docs that changed for that slice |

Avoid: dumping all peer-review + findings edits on every push unless something actually changed — that adds noise and eats Bugbot budget.

---

## Verdict on your question

| Question | Answer |
|----------|--------|
| Do we pass MD files as diff? | **Yes**, if they’re committed in the PR |
| Do Greptile/Bugbot use them as full plan context? | **Partially** — diff yes; full authority only with `files.json` / `BUGBOT.md` links |
| Is this in our plan today? | **Implicitly** (same PR, doc sync RQ8); **not** explicit review-context wiring |
| Should you keep MD in the PR? | **Yes** — for humans + iterative Greptile passes; wire context for bots |

If you want, next step can be either:
1. **Add `.greptile/files.json` + `.cursor/BUGBOT.md`** and then run **RQ0 only** + local Bugbot + push fresh branch, or  
2. Skip the wiring and proceed RQ0 with docs-in-diff only (still fine; slightly less bot context).

---

**User**

seesm great. likley we need add this to execute rules?

---

**Cursor**

Checking where execution and review-context rules live in the repo so we can recommend the right place.


Yes — add it to the execution plan, not to general `.cursor/rules`. Wiring it in RQ0 as repo config plus a short execution contract.


Yes — but **execution plan**, not general Cursor rules.

| Where | Add? | Why |
|-------|------|-----|
| **`REVIEW_QUALITY_EXECUTION.md`** | **Yes** | Contract for this program: what to ship, when, and how commits should look |
| **`.greptile/files.json` + `.cursor/BUGBOT.md`** | **Yes (RQ0)** | Actual wiring Greptile/Bugbot read |
| **`.cursor/rules/`** | **No** | IDE-agent only; Bugbot does not use them |
| **`phase-execution` skill** | Optional later | Only if you want this pattern for every future program PR |

I added to the execution doc:

1. **Locked decision** — RQ0 ships review-context wiring; per-phase commits = code + minimal status updates.
2. **New section** — `PR review context (Greptile + Bugbot)` with the table and commit pattern.
3. **RQ0 deliverables** — explicit `.greptile/files.json` and `.cursor/BUGBOT.md` files + paths to execution/findings.
4. **Peer-review table** — row 18 for pass 2 traceability.

So when you run `/phase-execution` on RQ0, the agent should create the migration **and** the two config files in the first commit, then pause after migration per LOOP.

Want me to start RQ0 implementation next?

---

**User**

imho it is worth

phase-execution skill
Optional later

---

**Cursor**

Adding the Greptile/Bugbot review-context pattern to the phase-execution skill.


Adding a dedicated section to `phase-execution` and a matching contract in `create-execution-plan` so new plans bake it in from the start.


Agreed — it’s worth baking into the skills, not just the review-quality execution doc.

**`phase-execution` skill** — new **PR review context (Greptile + Bugbot)** section:
- Wire `.greptile/files.json` + `.cursor/BUGBOT.md` on the **first LOOP iteration**
- Default targets: execution file, findings, optional authority doc
- Per-phase commits: code + minimal README status (not full doc churn)
- Explicit: not `.cursor/rules/`
- LOOP step 3: first iteration ensures wiring exists
- Execution doc contract points back to this section

**`create-execution-plan` skill** — so future plans get it by default:
- Optional template block **PR review context** (required when code + docs ship together)
- Checklist item for first-phase wiring

Together with `REVIEW_QUALITY_EXECUTION.md`, the chain is: **plan author** → **execution doc** → **phase-execution agent** → **first commit ships wiring**.

Ready to start RQ0 when you are.

---

**User**

also add in our plans or thing to improcve such functionality. imho it is gerat

like there and maybe anoter docs or we expand our plan and add in this wave?

docs/review-pipeline/review-quality/REVIEW_QUALITY_STRUCTURAL_CONTEXT.md

---

**Cursor**

Reviewing the wave and structural-context docs to find the best place to capture this improvement.


Creating a sibling strategy doc (like structural context) and linking it across the wave plans.


Good call — I treated it like structural context: a dedicated strategy doc plus wave hooks, not buried only in RQ0.

### New doc (sibling to structural context)

**[`REVIEW_QUALITY_REVIEW_CONTEXT.md`](docs/review-pipeline/review-quality/REVIEW_QUALITY_REVIEW_CONTEXT.md)**

- **RC track** — engineering context (what the PR should implement) vs **SC track** (code graph / callers)
- **v0 (RC0)** — RQ0 ships `.greptile/files.json` + `.cursor/BUGBOT.md`
- **Improvement ladder** — RC1 scoped doc subsets, RC2 active RQ pointer, RC3 cascading rules, RC4+ `.revy/rules` product
- **RQ-RC-1** — post-`review-quality-v1` PR when dogfood metrics warrant it
- Q-registry, success metrics, honest positioning

### Cross-links added

| Doc | Change |
|-----|--------|
| `REVIEW_QUALITY_STRUCTURAL_CONTEXT.md` | RC companion layer + SC8 tie-in; Next step for RQ-RC-1 |
| `REVIEW_QUALITY_FINDINGS.md` | RC Q-registry; parking lot → RQ-RC-1 |
| `review-quality/README.md` | RC track + doc in index |
| `REVIEW_QUALITY_GENERAL_PLAN.md` | Post-v1 RC pointer |
| `REVIEW_QUALITY_EXECUTION.md` | Out of scope: RQ-RC-1; RQ8 doc-sync row |
| `waves/README.md` | Post-v1 table: RQ-STRUCT-1 + **RQ-RC-1** |
| `REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md` | New § PR review context |
| `REVIEW_PIPELINE_PRODUCT_PATTERNS.md` | Dogfood exception + planning-doc row |

### Wave shape

- **This wave (RQ0–RQ8):** ship RC0 only
- **After tag:** optional **RQ-RC-1** (same program folder, separate PR) — parallel to RQ-STRUCT-1

Same pattern as structural context: strategy doc now, execution file when dogfood proves the need.

---

**User**

let 's decide next steps. mplemnt one phase, bugbbot local review, new branch and ship? both are enabled greptile and revy. ?

we want process step by step to capture all we can

---

**Cursor**

Checking the repo state and execution plan so we can define a concrete step-by-step process.


Agreed. Here’s a concrete process that matches the execution plan, migration pause, and dogfood (Greptile + Revy + Bugbot).

## Decision

| Question | Answer |
|----------|--------|
| **One phase at a time?** | Yes — start with **RQ0 only** |
| **One PR or many?** | **One PR** (`feat/review-quality`) — S1 locked; each RQ = one commit on same PR |
| **Bugbot before push?** | Yes — local Bugbot on branch diff, fix blockers, then commit/push |
| **Greptile on PR?** | Yes — after push; wired via `.greptile/files.json` (ships in RQ0) |
| **Revy on PR?** | Yes — autostart runs **current** pipeline on the PR until RQ3+ land; still useful for baseline noise |
| **Stop after RQ0?** | **Yes** — migration pause; you apply `0026` on staging before RQ1 |

## Current repo state

You’re on **`fix/reconcile-enum-str`**, not `feat/review-quality`. Planning docs + skill updates are **uncommitted**. No `.greptile/files.json` or `.cursor/BUGBOT.md` yet.

**First move:** fresh branch from `main` (or stash/commit docs off the reconcile branch first).

---

## Step-by-step (repeat per RQ phase)

### 0 — Prep (once)

1. `git checkout main && git pull`
2. `git checkout -b feat/review-quality`
3. **Commit planning baseline** (all review-quality docs + skill updates) — separate from RQ0 code so Bugbot/Greptile aren’t drowning in 20 MD files in the first code commit  
   - Message: `docs(review-quality): baseline findings, execution, RC/SC strategy`
4. Open PR early (optional but good for Greptile/Revy from commit 1)

### 1 — RQ0 implement

1. Read `REVIEW_QUALITY_EXECUTION.md` § RQ0 only
2. Hand-written migration `0026` + ORM models + enums
3. `tests/unit/test_review_quality_models.py`
4. **`.greptile/files.json`** + **`.cursor/BUGBOT.md`** (execution + findings, `backend/**`)
5. Minimal doc touch: `waves/README.md` → RQ0 in progress

### 2 — Local gates (before commit)

```bash
cd backend && pipenv run pytest tests/unit/test_review_quality_models.py -q
pipenv run ruff check --fix . && pipenv run ruff check .
```

### 3 — Local Bugbot

- Run `/review-bugbot` (or Bugbot subagent) with `Diff: uncommitted changes` (or `branch changes` after staging)
- Fix **blockers**; re-run pytest + ruff
- Note findings in a scratch log (see §5)

### 4 — Ship RQ0

```text
feat(review-quality): RQ0 schema migration + review context wiring
```

- `git push -u origin feat/review-quality`
- PR open if not already (title e.g. `feat(review-quality): diff-first + pipeline trace (WIP)`)

### 5 — Capture learnings (each phase)

After push, log in [REVIEW_QUALITY_REVIEW_CONTEXT.md](docs/review-pipeline/review-quality/REVIEW_QUALITY_REVIEW_CONTEXT.md) dogfood metrics (or a short PR comment):

| Signal | RQ0 expectation |
|--------|-----------------|
| Bugbot cited execution/findings? | Should flag schema/route mismatches |
| Greptile thread quality | Did it use wired docs vs generic advice? |
| Revy run on PR | Baseline only until later RQs merge |
| False positives | Note for RC1 (scoped doc subsets) |
| Missed issues | Note for BUGBOT.md / files.json gaps |

### 6 — Human gate (RQ0-specific **STOP**)

- Apply migration `0026` on **staging**
- Confirm workers start clean
- **Do not start RQ1** until you confirm

### 7 — Resume LOOP

Same branch, same PR:

```text
/phase-execution from RQ1
```

Repeat steps 1–6 for RQ1…RQ8 (no migration pause except RQ0).

---

## Three reviewers — who does what when

```text
RQ0 local:  pytest → ruff → Bugbot (reads BUGBOT.md)
     ↓
RQ0 push:   Greptile (reads files.json) ∥ Revy autostart (old pipeline)
     ↓
You:        apply migration 0026 on staging
     ↓
RQ1:        same PR, next commit …
```

| Reviewer | When | Context |
|----------|------|---------|
| **Bugbot** | Pre-commit, local | `.cursor/BUGBOT.md` → execution + findings |
| **Greptile** | Post-push, on PR | `.greptile/files.json` |
| **Revy** | Post-push, on PR | Current prod pipeline; new behavior lands RQ1+ |

---

## Commit plan for this PR (sketch)

| # | Commit | Contents |
|---|--------|----------|
| 1 | `docs(review-quality): baseline` | Findings, execution, RC/SC, skills (optional split) |
| 2 | `feat(review-quality): RQ0 …` | Migration + models + tests + greptile + bugbot |
| 3–10 | `feat(review-quality): RQ1 …` … `RQ8` | One per phase |
| — | Tag after merge | `review-quality-v1` |

---

## Recommended immediate next step

1. **You confirm:** branch from `main`, docs-first commit OK?
2. **I run RQ0:** implement + local Bugbot + push + open/update PR
3. **You:** apply `0026` on staging, then say “resume RQ1”

If that works, reply **“go RQ0”** (and whether to include the docs baseline commit in the same session). I’ll handle branch setup, implementation, Bugbot, and ship.

---

**User**

proceed. make all actuons needed, git, code etc

---

**Cursor**

Starting RQ0: checking the repo state and existing migration/model patterns.


Setting up the branch and implementing RQ0.


**RQ0 is shipped.** Migration pause — do not start RQ1 until staging migration is applied.

## What landed

| Step | Result |
|------|--------|
| Branch | `feat/review-quality` from `main` |
| Docs baseline | `1ea0bdf` — planning corpus + skills |
| **RQ0** | `64f661c` — migration `0026`, ORM models, enums, tests, Greptile/Bugbot wiring |
| PR | https://github.com/raimondskrauklis/revy/pull/50 |
| Local gates | 8 pytest passed, ruff clean, Bugbot no findings |

## RQ0 deliverables

- **Migration** `0026_review_quality` — pipeline tables, `base_sha`, index mode columns, `content_hash`, `evidence_snippet`, `resolution_status`, `summary_json`
- **Models** — `github_pipeline.py` + updates to index/revision/finding/chunk/publish models
- **Enums** — `GitHubIndexMode`, `PipelineStepType`, `PipelineStepStatus`, `PipelineArtifactKind`, `ResolutionStatus`
- **`.greptile/files.json`** + **`.cursor/BUGBOT.md`** → execution + findings for `backend/**`

## Your turn (human gate)

1. **Staging migration:**
   ```bash
   cd backend && pipenv run alembic upgrade head
   ```
2. Confirm workers restart clean after `0026`
3. Watch **Greptile** + **Revy** on [PR #50](https://github.com/raimondskrauklis/revy/pull/50) — note what they catch vs miss (RC dogfood metrics)
4. When staging is green, say **“resume RQ1”** and I’ll continue the LOOP on the same PR

**STOP here** per migration pause rule — RQ1 (diff + compare) waits on your staging confirmation.

---

**User**

rtevy started automaticaly and gave response. (prev deploy of corse, no new updates we shipng now). just was not visible in progress sping like greptile and bugbot have (but appeard after)



---

**Cursor**

Checking PR #50 checks and the Revy review outcome to add context.


Good observation — that matches how Revy works today on the **deployed** stack (not this PR’s code yet).

## Why Revy has no “in progress” spinner

Greptile and Bugbot register GitHub checks that go **`queued` → `in_progress` → `completed`**.

Revy does something different: `create_check_run` posts **one** check with `status: "completed"` and the final conclusion only at **publish** time — after index → review → reconcile → judge → publish.

```189:196:backend/app/integrations/github_api.py
        json={
            "name": CHECK_RUN_NAME,
            "head_sha": head_sha,
            "external_id": external_id,
            "status": "completed",
            "conclusion": conclusion,
            "output": {"title": title, "summary": summary},
        },
```

So on PR #50:

| Check | In-progress UI | When it appears |
|-------|----------------|-----------------|
| **Greptile** | Yes (spinner ~5m) | Start → finish |
| **Bugbot** | Yes | Start → finish |
| **revy/review** | **No** | Only when the full pipeline finishes |

That’s a product gap, not a Greptile/Bugbot wiring issue. A natural fix is an early `in_progress` check at pipeline start (RQ3 publish polish or a small pre-RQ1 item).

## PR #50 status (useful dogfood)

| Check | Result | Note |
|-------|--------|------|
| CI tests | Pass | New migration + models are fine |
| **Greptile** | Pass | 37 files, 6 comments |
| **revy/review** | Fail | Expected — **old deploy** reviewed the PR |
| Deploy | Skipped | Normal for PR |

Revy’s finding (“full-revision RAG instead of diff-first” in `github_review.py`) is **correct for current prod** — that’s exactly **RQ1** scope. Good sign that autostart + publish work; the check just lands all at once with no spinner.

## Capture for later

Worth logging in [REVIEW_QUALITY_REVIEW_CONTEXT.md](docs/review-pipeline/review-quality/REVIEW_QUALITY_REVIEW_CONTEXT.md) dogfood log:

- **RC-D1:** Revy check has no `in_progress` — visibility gap vs Greptile/Bugbot  
- **RC-D2:** Pre-deploy Revy still reviews planning PRs usefully (intent vs code drift)  
- **RC-D3:** Greptile wired context finished; compare comment quality when you triage the 6 threads  

**Still on migration pause** — apply `0026` on staging when ready, then **“resume RQ1”**. I can add the dogfood log lines in the next commit if you want them in-repo now.

---

**User**

yes please log it. we need same as greptile and bugbot have

---

**Cursor**

Logging dogfood findings and adding a tracked requirement for Revy in-progress check runs like Greptile/Bugbot.


Logged and locked **G10** — Revy will get Greptile/Bugbot-style in-progress checks in this wave.

## Logged (PR #50 dogfood)

**[REVIEW_QUALITY_REVIEW_CONTEXT.md § Dogfood log](docs/review-pipeline/review-quality/REVIEW_QUALITY_REVIEW_CONTEXT.md#dogfood-log-pr-50)**

| ID | Finding |
|----|---------|
| **RC-D1** | No `revy/review` spinner — check only appears at publish end |
| **RC-D2** | Pre-deploy Revy still useful (full-RAG vs diff-first → RQ1) |
| **RC-D3** | Greptile RC0 wiring: pass, 6 comments |
| **RC-D4/D5** | CI + local Bugbot: pass |

Also mirrored in [CODE_REVIEW_LEARNINGS](docs/review-pipeline/REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md) and `actual_output_revy_greptile.txt` (captured on the branch).

## Locked: **G10** (ships in v1, not post-v1)

| Phase | What |
|-------|------|
| **RQ3** | `create_check_run(status=in_progress)` when pipeline starts; store `check_run_id` |
| **RQ7** | `update_check_run(status=completed, conclusion=…)` at publish (replace one-shot create) |
| **Failure** | Always finalize check — no orphan `in_progress` |

```text
enqueue → in_progress (visible on PR) → pipeline → completed at publish
```

Updated: execution plan, findings (G10), product patterns.

**Pushed:** `7eee843` on [PR #50](https://github.com/raimondskrauklis/revy/pull/50).

**Note:** Greptile flagged two migration FK issues (RESTRICT vs SET NULL on nullable pipeline FKs, `created_at` index for O8 purge). Worth fixing in RQ0 follow-up or early RQ1 — say the word if you want those addressed before staging migration.

---

**User**

i just copied this from github. gretpile is still good. thi is just info sinve we have plan to be close, but maybe some more obsercations (revy stll has old code)

docs/review-pipeline/review-quality/actual_output_revy_greptile.txt

also you can /babysit-pr 

and check do you get all details greptile and revy (maybe need more oernssions and get more info eyc) anlyse and also update findings and lessons

or cteae new file in this folder dedicated to thos improvemnts and we wil documnt what is good, what neds updates paralell for next waves

---

**Cursor**

Analyzing the captured output, fetching Greptile threads on PR #50, and triaging valid fixes vs documentation.


Fixing valid Greptile P1/P2 schema issues, then creating a dedicated dogfood analysis doc.


## Babysit PR #50 — complete

Pushed `b117202` with Greptile fixes + new dogfood doc.

### Greptile triage

| Severity | Location | Finding | Action |
|----------|----------|---------|--------|
| P1 | `0026_review_quality.py` | Nullable FKs need `ON DELETE SET NULL` | **Fixed** |
| P1 | `github_pipeline.py` | ORM `ondelete` mismatch | **Fixed** |
| P1 | `0026_review_quality.py` | Missing `created_at` index (O8 purge) | **Fixed** |
| P2 | `0026_review_quality.py` | Historical jobs backfilled as `diff` | **Fixed** — backfill `full` |
| P2 | `0026_review_quality.py` | `revision_id` should CASCADE | **Fixed** |
| P2 | `0026_review_quality.py` | Artifact empty content allowed | **Fixed** — CHECK constraint |

### Revy (old deploy) — skipped

| Severity | Location | Finding | Action |
|----------|----------|---------|--------|
| error | `github_review.py` | Full RAG not diff-first | **Skipped** — RQ1 |
| warning | `README.md` | Dependency baseline | **Skipped** — doc polish RQ8 |
| warning | `FINDINGS.md` | Encryption/redaction | **Skipped** — parking (O-sec) |
| warning | `EXECUTION.md` | Duplicate index jobs | **Skipped** — verify AS1 in RQ1 |

---

## New doc: dedicated dogfood tracker

**[REVIEW_QUALITY_DOGFOOD_PR50.md](docs/review-pipeline/review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md)**

- What `gh`/GraphQL can fetch vs what needs Revy UI paste
- Greptile vs Revy comparison
- What's good / what needs parallel waves (G10, RQ1, RQ3, RC-API)
- Per-phase table to extend after each RQ commit

Your paste file stays as raw artifact: `actual_output_revy_greptile.txt`.

---

## API / permissions takeaway

| Tool | Via `gh` | Gap |
|------|----------|-----|
| **Greptile** | Full threads + check summary | None for babysit |
| **Revy** | Check table + link only | Pipeline trace + full messages need Revy UI until **RQ3 GET** |
| **Bugbot** | Not on GitHub Checks | Local pre-push only |

No extra GitHub permissions needed for Greptile babysit. For Revy automation later: **RC-API** (expose run metadata) after RQ3.

Greptile should re-run on `b117202` — confidence should improve now that P1s are fixed. Still on **migration pause** until you apply `0026` on staging.

---

**User**

check alo greptile visual vs revy (bugbot actualy was kind same as greptile) sure we not have landed or plan yet but greptile visaualy/context etc is what we are tackling



---

**Cursor**

Comparing Greptile vs Revy publish UX against the codebase and updating the dogfood docs with a visual/context gap analysis.


Adding a visual/context UX comparison to the dogfood doc and learnings, mapped to the RQ7 Greptile-shaped publish plan.


You're right — **Greptile and Bugbot are the UX bar**; Revy today is a different (thinner) surface. Logged in [REVIEW_QUALITY_DOGFOOD_PR50.md § Visual UX](docs/review-pipeline/review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md#visual--context-ux--greptile--bugbot-vs-revy-target-bar) (`a91206a`).

## What you're seeing on PR #50

| | **Greptile / Bugbot** | **Revy (prod today)** |
|--|----------------------|------------------------|
| **While reviewing** | Check spins `in_progress` | Nothing until pipeline finishes (**G10**) |
| **Triage surface** | Long summary: narrative, confidence, “files needing attention” | Check body = **4-column table** + `Open in Revy` |
| **On the code** | **P1** badge on the line, diff hunk, explanation citing **AS1** | Inline only error/critical; warnings/docs → table row only |
| **Action** | `suggestion` blocks, **Resolve conversation** | Edit in Revy app |
| **Context** | Reads execution via RC0 (`files.json`) | Code behavior only — no planning-doc wiring |

Your Greptile screenshot is exactly what we want: P1 on `index_mode` default, explains AS1 manual → `full`, flags regression before RQ1 wires job-create. That's **engineering-context review** working.

Revy's screenshot is what we have now:

```156:180:backend/app/services/github_publish.py
def build_summary_markdown(
    ...
    lines = [
        "## Revy review summary",
        "",
        f"[Open in Revy]({_revy_ui_link(pull_request_id)})",
        "",
        "| Severity | Category | Title | File |",
```

Title + file in GitHub; full message and workflow behind the link.

## Not landed yet — but planned (RQ7 **G** track)

| Gap | Wave |
|-----|------|
| In-progress check | **G10** (RQ3 + RQ7) |
| Narrative + confidence 0–5 | **G2**, **G5** formatter (RQ7) |
| Full Greptile comment vs compact check | **G3** split (RQ7) |
| P-badge inline + explanation + suggestions | **G6/G7** + R6 blocks (RQ7) |
| “Fixed since last push” | **G9** (RQ6 → RQ7) |

**RC-D6** added to dogfood log. **CODE_REVIEW_LEARNINGS** updated: target is **RQ7**, not “R9+ someday”.

## New Greptile thread (not a babysit fix in RQ0)

P1 on `github_index_job.py`: column default `diff` ≠ AS1 manual `full` at **job create** → **RQ1** (set `index_mode` when enqueueing, not only ORM default).

**Bottom line:** Greptile/Bugbot = triage + inline context on GitHub. Revy = table + app link until RQ7. That's the product gap this wave is meant to close.

---

**User**

not forget run 'local' bugbot before each push. also can contribute for our lessons or other docs when we thjnk about agents. lke prompts etc. composer 2.5 (you) is EXTREMALY good at magaing agents. can paralely start to distilate this aspect from you as well

---

**Cursor**

Documenting mandatory local Bugbot before each push and distilling agent-orchestration patterns from this program into skills and learnings.


Logged and wired into skills. Pushed `d79d05f` on PR #50.

## Local Bugbot — now a hard gate (every push)

Updated skills/commands:

| Skill / command | Change |
|-----------------|--------|
| **`phase-execution`** | New § Local Bugbot before every commit/push |
| **`ship-changes`** | Step 3: Bugbot before commit; babysit → Bugbot again before fix push |
| **`babysit-pr`** + command | Step 6: Bugbot after Greptile fixes, before push |

```text
pytest → ruff → phase gate → LOCAL BUGBOT → commit → push
                                    ↑
                          Greptile/Revy run after push only
```

## New doc: agent orchestration learnings

**[REVIEW_QUALITY_AGENT_ORCHESTRATION.md](docs/review-pipeline/review-quality/REVIEW_QUALITY_AGENT_ORCHESTRATION.md)**

Distilled from PR #50 + this session:

- **Golden rule** — Bugbot pre-push; Greptile post-push
- **Parent agent discipline** — scope, LOOP stops, context budget, when to use subagents vs direct tools
- **Safe parallelism** — human migration + Greptile on PR; not Bugbot + half-done code
- **Prompt templates** — Bugbot `Custom Instructions` pointing at execution § RQn; phase-execution invoke; babysit-pr
- **Per-phase checklist** — copy-paste for LOOP
- **Anti-patterns** — push without Bugbot, doc churn every commit, skip migration pause

Linked from: `review-quality/README`, `DOGFOOD_PR50`, `CODE_REVIEW_LEARNINGS`.

## Evolve over time

The orchestration doc has a **Next** section for per-RQ prompt templates and Revy API babysit — we can append as RQ1+ runs. If you want this promoted to `AGENTS.md` later (repo-wide, not just review-quality), say when RQ8 doc-sync lands.

---

**User**

maybe agents deserve own folder what we we will update as we go?

---

**Cursor**

Creating a dedicated `docs/review-pipeline/agents/` folder and moving orchestration content there with a living README index.


Yes — dedicated living folder. Pushed `4525f7a`.

## `docs/review-pipeline/agents/`

| File | Purpose |
|------|---------|
| **[README.md](docs/review-pipeline/agents/README.md)** | Hub — what lives here, when to update, links |
| **[ORCHESTRATION.md](docs/review-pipeline/agents/ORCHESTRATION.md)** | LOOP, Bugbot gate, parent discipline, anti-patterns |
| **[PROMPTS.md](docs/review-pipeline/agents/PROMPTS.md)** | Copy-paste templates — **RQ0 filled**; stubs for RQ1, RQ7 |

**Planned later** (listed in README): `SUBAGENTS.md`, `DOGFOOD_INDEX.md`

## Wiring

- Skills → `agents/ORCHESTRATION.md` + `PROMPTS.md`
- [AGENTS.md](AGENTS.md) — new “Agent orchestration (living)” row
- [review-pipeline/README.md](docs/review-pipeline/README.md) — folder in layout tree
- Dogfood stays in `review-quality/` (PR-specific); agents folder links to it

## As you go

Each RQ phase: add a **PROMPTS.md** section + optional dogfood row. Hard gate changes → update **skill + ORCHESTRATION** in the same commit.

---

**User**

let 's say we not hurry in this project. outcomes distillatin is very import part of our workflow. we want get best and create awesome app for us.

---

**Cursor**

Capturing this as explicit workflow principles in the agents folder so every future LOOP inherits it.


That matches how we should run this program — and it’s already showing up in what we built.

**Not hurry** means:
- RQ0 shipped + **stop** (migration pause) — not “blast through RQ8 tonight”
- Greptile babysit + dogfood docs **before** RQ1
- RQ7 Greptile-shaped UX because we **looked** at PR #50, not because a checklist said so

**Outcomes distillation** is a deliverable, not a nice-to-have:
- `agents/` — LOOP, prompts, principles
- `REVIEW_QUALITY_DOGFOOD_PR50.md` — visual gap, triage tables
- Skills updated when we learn (Bugbot before every push)
- Three reviewers compared, not “Greptile said fix it” alone

**Awesome app for us** = dogfood on `feat/review-quality` is the product spec. If Revy’s check is a thin table and Greptile’s is P1 on the line citing AS1, **RQ7** is the answer — we already locked that from screenshots.

I added a **Principles** section to [agents/README.md](docs/review-pipeline/agents/README.md) so future sessions inherit this, and nudged [review-quality/README.md](docs/review-pipeline/review-quality/README.md) status to “distillation first; RQ0 done; migration pause.”

**Current state (healthy, not rushed):**
| Done | Waiting |
|------|---------|
| RQ0 code + Greptile fixes + learnings | You: `0026` on staging |
| PR #50 open, Greptile/Revy dogfood captured | Resume RQ1 when ready |
| Agents folder + prompts for RQ0 | Add RQ1 block when we start |

When you’re ready for RQ1, say the word — same rhythm: implement → Bugbot → push → dogfood row → pause if needed. No rush on my side either.

---

**User**

decide is it worth? it adds lead to agent and fills comntext but also bring huge value imho?
If you want this promoted to AGENTS.md later (repo-wide, not just review-quality), say when RQ8 doc-sync lands.

---

**Cursor**

**Verdict: worth it — but promote in layers, not all at once.**

## Context cost vs value

| Approach | Context hit | Value |
|----------|-------------|--------|
| Duplicate `ORCHESTRATION.md` into `AGENTS.md` | **High** — every chat, even a one-line frontend fix | Low ROI |
| **One row** in Read first (what you have now) | **~1 line** | Good pointer; agents opt in |
| **Short § at RQ8** (~8–12 lines: principles + when to read `agents/`) | **Medium** — only after patterns are battle-tested | High for all future program work |
| Skills already encode gates | Loaded when skill runs | Best ROI — no AGENTS bloat |

The folder + skills are the real win. `AGENTS.md` should stay a **router**, not a second copy of orchestration.

## Recommendation

| When | What |
|------|------|
| **Now (keep)** | Single Read-first row → `docs/review-pipeline/agents/README.md` ✓ already in `AGENTS.md` |
| **Now (optional, small)** | Skills table: `phase-execution` also points at `waves/REVIEW_QUALITY_EXECUTION.md`, not only scaffold |
| **RQ8 doc-sync** | Add **## Program execution (agents)** to `AGENTS.md`: 3–4 bullets (distill outcomes, Bugbot before push, read `agents/` only on LOOP), link to `agents/README.md#principles` |
| **Not worth** | Inlining dogfood PR #50, Greptile visual tables, or full PROMPTS into `AGENTS.md` |

## Why wait for RQ8 on the bigger §

By RQ8 you’ll have:
- Several RQ prompts in `PROMPTS.md`
- Dogfood rows proving the workflow
- G10 / visual gaps validated or adjusted

Then the `AGENTS.md` blurb is **stable**, not churning every RQ.

## Bottom line

**Huge value** — capture in `agents/`, skills, dogfood. **AGENTS.md** gets a thin pointer now and a **short promoted section at RQ8**, not a wall of text today. That balances context budget with “every agent knows this exists.”

Uncommitted locally: **Principles** in `agents/README.md` + review-quality README pace line — worth committing on the next doc pass (with or without the Skills table tweak). Want me to commit that small `AGENTS.md` Skills update now?

---

**User**

too much messy prompt from me, zoom out, look form platform perspective and organise all what i wrote and you aligned with how YOU thinnk should be organised. forming constince and effectveness. You are extremaly smart and will advice bes. also not overingeneer. 

---

**Cursor**

Reviewing how docs and skills are organized today, then proposing a clean platform-level structure.


Consolidating into one platform map in `agents/README.md` — the single zoom-out doc. No new files.


Here’s the zoomed-out view — organized, not over-engineered.

## The whole thing in one sentence

**Build the product from locked contracts; run it on ourselves; capture what we learn; let three reviewers sharpen each push.**

---

## Four layers (never mix them)

| Layer | Question | Home |
|-------|----------|------|
| **Contract** | *What* are we building? | `FINDINGS` + `EXECUTION` § RQn |
| **Process** | *How* do we ship one slice? | `agents/` + skills |
| **Wiring** | *How* do bots read the contract? | `.greptile/`, `BUGBOT.md` |
| **Evidence** | *What* did we learn on a real PR? | `DOGFOOD_PR50`, learnings doc |

Strategy docs (structural context, review context) are **post-v1** — read when relevant, not every session.

---

## One RQ loop (repeat until tag)

```
Contract (RQn) → code → test → Bugbot → push → Greptile/Revy → babysit → distill → [pause?] → next RQ
```

**Distill** = one dogfood row + prompt block if needed. Not a separate project — part of “done.”

**Pause** = migration, staging, human — not failure.

---

## Three reviewers (complementary)

| | When | Strength |
|--|------|----------|
| **Bugbot** | Before push | Fast, local, blocks dumb mistakes |
| **Greptile** | After push | Contract, schema, inline P-badges |
| **Revy** | After push | Real pipeline on deploy (lags branch until we ship) |

Greptile/Bugbot = **target UX** for GitHub (RQ7). Revy today = thin table; that’s the gap we’re closing, not ignoring.

---

## What we cut (anti–over-engineering)

- No `DOGFOOD_INDEX`, `SUBAGENTS` files until pain appears
- No duplicating contract into `agents/`
- No fat `AGENTS.md` until **RQ8** — one pointer row is enough now
- No rushing RQ1 before staging `0026` + a dogfood note

---

## Canonical doc

Everything above lives in **[agents/README.md](docs/review-pipeline/agents/README.md)** — the platform map. One page; update as we learn, not a new doc every idea.

**You:** migration pause. **Us (when ready):** RQ1, same loop.

---

**User**

/babysit-pr 



---

**Cursor**

One open Greptile P1: set `index_mode` at job creation per AS1. Applying a minimal fix at both create sites.


Babysit pass complete on [PR #50](https://github.com/raimondskrauklis/revy/pull/50). One open Greptile thread; fixed and pushed as `87c50d2`.

| Severity | Location | Finding | Action |
|----------|----------|---------|--------|
| P1 | `github_index_job.py` | Admin manual index jobs silently default to `diff` after RQ0 migration | **Fixed** — ORM + migration `server_default` → `full`; explicit `index_mode=full` in `create_index_job`; explicit `index_mode=diff` in `maybe_enqueue_pipeline_for_revision` |
| P1 | `0026_review_quality.py` | Missing `created_at` index for O8 purge | Already resolved (`b117202`) |
| P1 | `0026_review_quality.py` / `github_pipeline.py` | Nullable FKs need `ON DELETE SET NULL` | Already resolved (`b117202`) |
| P2 | `0026_review_quality.py` | Historical rows backfilled as `diff` | Already resolved (`b117202`) |
| P2 | `0026_review_quality.py` | `revision_id` FK should CASCADE | Already resolved (`b117202`) |
| P2 | `0026_review_quality.py` | Artifact content CHECK constraint | Already resolved (`b117202`) |

**Gates:** ruff clean · 23 targeted tests passed · local Bugbot clean.

Greptile should auto-resolve the remaining thread on the next review pass. Full RQ1 work (`IndexTriggerRequest.mode`, compare API, deep/critical guards) remains scoped to RQ1.

---

**User**

i don't know do you see agents your launchig thougts but apriach is interestng. when we will achive agents will be interting to see but we need build findings already imh

like current bugbot thing (local bugbot never catches all errors. it is different than gugbot in github - guthub bugbot always fnd bugs vere local not (greptile as well) so layered is sure waht we are looking for.

lats tash thoughts. als we need check what tools he uses. likley gre abd nb sarch when needed - but You know MUCH better i'm just speculating

I am reviewing the provided diff for bugs.

The diff changes index_mode defaults from "diff" to "full" across the migration, ORM, and indexing service. I am checking whether this change introduces bugs.

Pipeline jobs explicitly use GitHubIndexMode.diff. Tests assert this mode. I need to check if other code paths create index jobs without setting index_mode, and whether the worker logic depends on diff versus full. I also need to verify if the migration backfill conflicts with the old server_default.

Investigating the diff against the review-quality contract and all code paths that create or use index_mode.

Bugbot found no bugs.


---

**Cursor**

Distilling your layered-review observations into the findings corpus and checking what local Bugbot actually uses versus GitHub.


Capturing the layered-review insight in findings and clarifying what local Bugbot actually does versus GitHub.


You're right on all counts — stashed in [DOGFOOD_PR50 § layered reviewers](docs/review-pipeline/review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md#layered-reviewers--complementarity-pr-50), **RC-D4/D5** in learnings, and a note in [ORCHESTRATION](docs/review-pipeline/agents/ORCHESTRATION.md).

**Layered is the design, not a failure**

| Layer | Job |
|-------|-----|
| Local Bugbot | Fast pre-push hygiene — obvious bugs in the diff |
| Greptile | Contract/spec — RC0 execution docs, AS1, migration semantics |
| GitHub Bugbot | Deeper PR review — often finds things local skipped |
| Revy | Product truth on **deployed** code |

No single layer should catch everything. The `index_mode` case is the textbook example: local Bugbot reasoned correctly (“pipeline sets `diff`, manual should be `full`”) and said **no bugs** on the fix — which was right for that diff. Greptile had already caught the **AS1 contract regression** before babysit. That's complementarity working.

**Local Bugbot ≠ GitHub Bugbot**

From what we can see:

- **Local** — one Cursor `bugbot` subagent pass, `.cursor/BUGBOT.md` + diff, read/grep across the repo (your pasted reasoning shows it checking other job-create paths and migration backfill). No documented multi-pass or agentic LSP loop.
- **GitHub** — different pipeline: PR context, multiple passes / shuffled-diff voting, agentic tool loop (pull definition, call sites) per our [arch notes](docs/review-pipeline/code-review-arch_perplexity_searcj_advice_only.md).

So “GitHub Bugbot always finds something, local often doesn't” matches expectations — local is a **gate**, not a completeness check.

**On agent orchestration**

The subagent launch pattern (parent implements → Bugbot → Greptile babysit → distill) is useful dogfood for how Revy should work in RQ4+. But you're right: the product work is **building the findings corpus and shipping RQ loops**, not perfect agent theater. Agents get interesting when Revy itself can run a similar stack on customer PRs.

**What to build from this (already in findings)**

1. Keep local Bugbot as hard pre-push gate — cheap, catches slop.
2. Never treat local green as “done” — Greptile + GH Bugbot + Revy add orthogonal signal.
3. RC0 wiring is why Greptile beats local on contract issues — Revy needs the same (RQ-RC-1 / product rules).
4. RQ4+ product target: diff generator + spec-aware judge + optional agentic trace — not one-shot review.

Docs updated locally; not committed unless you want them in the PR.

---

**User**

not rely. don 't drift. what we do is tung revy to handle githubs bugbot/greptile and create own workflows we jsut run in paralell and get ides how to improwe own (github local is likly to saty since it is included in cursor)

what we do is distilate what they do good and how. imho under hood bithub nugbot/greptile also run agents kinda like local bugbot (maybe for hatder cases not low, don 't know)

Layer	Job
Local Bugbot
Fast pre-push hygiene — obvious bugs in the diff
Greptile
Contract/spec — RC0 execution docs, AS1, migration semantics
GitHub Bugbot
Deeper PR review — often finds things local skipped
Revy
Product truth on deployed code

---

**Cursor**

Correcting the framing: parallel runs are for distillation into Revy, not permanent reliance on external reviewers. Updating the docs.


Correct — I had drifted into “layered stack we rely on.” Updated framing in [ORCHESTRATION](docs/review-pipeline/agents/ORCHESTRATION.md), [DOGFOOD_PR50](docs/review-pipeline/review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md), [agents/README](docs/review-pipeline/agents/README.md), and **RC-D4/D5** in learnings.

**What we actually do**

```text
TODAY                         GOAL
─────                         ────
Run in parallel on our PRs    Tune Revy to absorb what works
Greptile                      → RC4 rules + RQ7 GitHub UX
GitHub Bugbot                 → RQ4+ trace/judge agents
Local Bugbot (Cursor)         → stays — dev gate, not Revy SKU
Revy (deploy)                 → the product
         │
         └── distill → findings → RQ waves
```

**Not:** four permanent layers customers need.  
**Yes:** parallel dogfood → note what each does well and how → ship it in Revy.

**Under the hood (hypothesis, not gospel):** Greptile and GitHub Bugbot are probably agent-shaped for harder findings — same class as local Bugbot (read/grep/trace), with more passes and PR context. Distillation job is copying **behaviors** (contract wiring, inline severity, trace-before-claim), not stacking vendors.

**Local Bugbot** stays because Cursor includes it — cheap pre-push hygiene while we build. It’s not “layer 1 of Revy.”

Docs are local only; say if you want them committed to PR #50.

---

**User**

and we have only github greptile not bugbot (just local bugbot) - but i have used github a lot and info i gave is corrcet

---

**Cursor**

Correcting docs: PR #50 uses Greptile on GitHub and local Bugbot only — GitHub Bugbot stays as reference knowledge from your experience.


Good correction — docs updated.

**PR #50 reality:**

| Tool | On #50? |
|------|---------|
| Greptile (GitHub) | Yes |
| Local Bugbot (Cursor) | Yes |
| Revy (deploy) | Yes |
| GitHub Bugbot | **No** |

**GitHub Bugbot** stays in docs as **reference only** — your experience on other repos + [arch notes](docs/review-pipeline/code-review-arch_perplexity_searcj_advice_only.md) for the deeper-review bar Revy should hit in RQ4+. Not claimed as something we run on #50.

Also fixed a broken Revy triage table header in the dogfood doc. Changes are local; say if you want them committed.

---

**User**

commit and push all

---

**Cursor**

Fixing a broken markdown table separator, then committing.


Pushed `e9a3508` to `feat/review-quality`.

**4 files:**
- `docs/review-pipeline/agents/ORCHESTRATION.md`
- `docs/review-pipeline/agents/README.md`
- `docs/review-pipeline/review-quality/REVIEW_QUALITY_DOGFOOD_PR50.md`
- `docs/review-pipeline/REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md`

Distillation framing, RC-D4/D5, #50 tooling reality (Greptile + local Bugbot only), and babysit pass 2 notes are all in. Also fixed the Revy triage table separator.

---

**User**

actualy i could disable revy not to burn tokens. since current behaviour we know and more interest in monitorng greptile. so no new revy feed fill appear.

---

**Cursor**

Checking how Revy autostart is configured so we can disable it during Greptile-focused dogfood.


---

**User**

i just suspend app on github

---

**Cursor**

Noting the GitHub App suspension in dogfood docs so we don't expect Revy runs on #50.


Makes sense. Suspending the GitHub App is the cleanest cut — no webhooks, no autostart, no `@revy review`, no token burn. Greptile + local Bugbot dogfood continues as-is.

RC-D2 already captured what old-deploy Revy does; nothing new to learn from Revy on every push until the branch is actually deployed.

**Re-enable when:** RQ1+ is on staging and you want smoke, or RQ8 human gate (autostart e2e).

Noted in dogfood + orchestration docs (local, uncommitted). Say if you want that committed.

---

**User**

this is green. likely we merge? we don t care about app uptime. we are in my testing only. 

pross - less tokens. cons - no plang docs - value not confirmed yet. also since we distilling we more care about behabiour rather a100% bugs cought. thoughts?

---

**Cursor**

Checking PR #50 state and what's gated before giving merge advice.


**Short answer:** RQ0 is merge-worthy as a **checkpoint** if you want schema on `main` and smaller future diffs. **Don’t merge** if you’re continuing RQ1 on the same branch this week — execution **S1** is one PR through RQ8.

---

### What “green” actually means here

| Check | Status |
|-------|--------|
| CI (lint/test) | Green |
| Greptile | Green — contract dogfood worked |
| `revy/review` | Red — old deploy; app suspended anyway → ignore |

RQ0 deliverable is done: migration `0026`, models, RC0 wiring, Greptile babysit clean, findings distilled.

---

### Your pro/con, sharpened

**Pro merge (less tokens)**  
- After merge, RQ1+ PRs are mostly `backend/**` — much smaller Greptile runs.  
- Planning corpus lands on `main` once; you stop paying to re-review 3k+ doc lines every push.  
- Solo testing, app suspended, deploy skipped — low blast radius.

**Con (“no planning docs”) — partly a false worry**  
`.greptile/files.json` points at repo paths, not the PR diff:

```1:13:.greptile/files.json
{
  "files": [
    {
      "path": "docs/review-pipeline/waves/REVIEW_QUALITY_EXECUTION.md",
      ...
      "scope": ["backend/**"]
    },
```

After merge, Greptile **still reads** execution + findings on `main` when reviewing backend changes. RC0 contract behavior should persist on RQ1 slices.

What you **lose** after merge: Greptile reviewing **doc churn in the diff** (README drift, etc.). That’s lower value — you already captured the important behaviors (AS1 inline, FK semantics, UX bar).

**Behavior vs bugs caught** — right lens for merge  
You’re not merging because Greptile found every bug. You’re merging because RQ0 proved:

- RC0 wiring → spec-aware findings (AS1 on `index_mode`)  
- Schema contract holds  
- Distillation corpus is written (RC-D4, dogfood, orchestration)

That’s enough for a checkpoint.

---

### Recommendation

| If… | Then… |
|-----|--------|
| Resuming RQ1 in days on same branch | **Stay open** — S1 one-PR; apply `0026` on staging, continue LOOP |
| Pausing or want `main` = schema baseline | **Merge RQ0** — tag later at RQ8; open RQ1 as same branch or `feat/review-quality-rq1` |
| Unsure | **Merge** — you’re solo, app suspended, dogfood goals for RQ0 met |

If you merge: note in PR body “RQ0 only — program continues; `review-quality-v1` at RQ8.” Commit the Revy-suspended doc notes first if you want that on `main`.

**Don’t block merge** on RC0 “unconfirmed” — confirm on the **first RQ1 code-only PR** after merge; that’s the real product shape anyway (customers don’t ship 3k lines of planning docs).

---

**User**

we will implement all phases. you will write code just now step by step. so what is advice?

---

**Cursor**

**Advice: don’t merge yet.** Keep [#50](https://github.com/raimondskrauklis/revy/pull/50) open on `feat/review-quality` and run RQ1→RQ8 on the same branch, same PR.

**Why (given you’ll implement everything step by step):**

| Merge now | Stay on one PR |
|-----------|----------------|
| Breaks **S1** (one PR / one `0026` chain) | Matches execution |
| RQ1+ is either direct to `main` or a **second** PR | Greptile + RC0 stay wired for every RQ slice |
| Checkpoint value is small — you’re not pausing the program | Merge once at **RQ8** + tag `review-quality-v1` |

**Token cost on a fat PR** is real but acceptable for this window — you’re distilling **behavior** (AS1, FK semantics, inline UX), and that’s already landed in dogfood docs. Future pushes are mostly backend; Greptile cost drops as doc churn stops.

**What to do now (in order):**

1. **Commit** the Revy-suspended doc notes (local, uncommitted).
2. **Human gate:** apply migration `0026` on staging + restart workers (when you’re ready for RQ1).
3. **Resume LOOP at RQ1** on `feat/review-quality` — same PR, phase-execution step by step.
4. **Merge** only after RQ8 human gate (S4 smoke, Greptile-shaped publish, etc.).

**Ignore for merge decision:** `revy/review` red (app suspended, old deploy). **Watch:** Greptile on each RQ commit; local Bugbot before push.

If you want, next step is commit suspend docs → you apply `0026` → say **phase-execution from RQ1** and we start coding.

---

**User**

migrations applied, ok we keep one pr till the end. proceed with next logical actiona

---

**Cursor**

Migrations are applied — proceeding with RQ1 per the execution plan. Reading the RQ1 contract and current branch state.


Starting RQ1 on `feat/review-quality` (through RQ8). Exploring the codebase and implementing RQ1 step by step.


Implementing diff-first indexing and review guards.


Fixing Bugbot finding: defer chunk deletes until after a successful embed.


