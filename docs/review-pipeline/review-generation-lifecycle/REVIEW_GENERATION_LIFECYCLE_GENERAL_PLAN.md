# Review generation lifecycle — general plan

**Baseline:** [REVIEW_GENERATION_LIFECYCLE_FINDINGS.md](./REVIEW_GENERATION_LIFECYCLE_FINDINGS.md) (peer-reviewed pass 2, 2026-07-28)  
**Prerequisite:** [github-surface-hardening P0–P4](../github-surface-hardening/) merged to `main` ([#53](https://github.com/raimondskrauklis/revy/pull/53), 2026-07-27).

**Thesis:** Greptile/Bugbot-class **snapshot semantics** — latest HEAD only, supersede in-flight generations, **publish after finish** (no spill on any GitHub channel). Revy pipeline architecture unchanged; generation **policy** hardened.

**Gap IDs:** **RG-*** in findings; **P0–P5** = program phases below.

**Locked:** RG-Q1 snapshot · RG-Q3 coalesce ≤10 s · RG-Q7 full surface flush · RG-Q8 neutral finalize · RG-Q9 `superseded` on review run · RG-Q10 judge per-finding · RG-Q11 stage-entry guards · RG-Q12 no enum migration.

---

## Cross-cutting (every phase)

- **Tests:** `backend/tests/unit/` each phase; dogfood scenarios from findings §13.
- **Tenancy:** workspace scope unchanged.
- **Trace:** log `publish_skipped_not_head`, `generation_superseded`; pipeline trace mirrors review run status.
- **i18n:** GitHub markdown English v1.
- **Docs:** README phase row; PRODUCT_PATTERNS generation row when P2 ships.
- **Schema:** new status values on existing `String(32)` columns — **no Alembic** unless adding CHECK (RG-Q12).

---

## P0 — Foundations (RG-9)

**Goal:** Generation lifecycle primitives — authority helpers, enum values, coalesce setting, smart-trigger guard.

**Scope — in:** `GitHubReviewRunStatus.superseded`; `GitHubPublishJobStatus.skipped_not_head` + `skipped_superseded`; `is_authoritative_for_pull_request_head(session, revision_id)`; `mark_review_runs_superseded_for_pull_request(session, pull_request_id, keep_revision_id)`; `mark_active_review_runs_superseded_for_revision(session, revision_id)` for command vs autostart on same HEAD; settings `review_coalesce_seconds` (0–10); smart-trigger guard documented in `github_generation_lifecycle` module docstring (`pull_request_review` does not enqueue pipeline).

**Scope — out:** HEAD gate (P1); G10 finalize (P2); Alembic unless CHECK constraints chosen.

**Deliverables:** Enum values + helper API + unit tests; trace field contract documented.

**Depends on:** GH hardening on `main`.

---

## P1 — HEAD-gated publish (RG-1, RG-10, RG-12)

**Goal:** Stale revision never writes GitHub surface; same-SHA re-publish works; superseded run caught at publish task entry.

**Scope — in:** `run_publish_job` — gate **before** `job.status = processing`; no GitHub writes when `job.head_sha != pull_request.head_sha` **or** review run `superseded` → `skipped_not_head` / `skipped_superseded`; skip path does not `record_publish_pipeline_step` as completed (P5.3); on skip-at-publish only: `finalize_pipeline_github_check_neutral` (P2 primary); `find_publish_job_for_head_sha` — **`completed` only**; `create_publish_job_for_review_run` skip when superseded; admin `create_publish_job` uses same `run_publish_job` gate; same-SHA retry when still HEAD.

**Scope — out:** Supersede marking on synchronize (P2); full surface buffer (P3).

**Deliverables:** Unit tests H1 blocked after H2 HEAD; pending job + supersede race; `@revy publish` retry after skip.

**Depends on:** P0.

---

## P2 — Generation supersede + stage-entry guards (RG-2, RG-7, RG-8, RG-11)

**Goal:** New `synchronize` supersedes prior generations; authority enforced at every stage entry; stale G10 checks finalized at supersede moment.

**Scope — in:** On new revision: `mark_review_runs_superseded_for_pull_request` **and** `mark_index_jobs_superseded_for_pull_request`; on **command** enqueue or **same-SHA synchronize**: `mark_active_review_runs_superseded_for_revision` **and** `mark_active_index_jobs_superseded_for_revision` (same HEAD revision); **`index_pull_request_revision`**: if not authoritative → skip entire pipeline-trace block (`ensure_pipeline_run_for_index_job`, G10, stash); index DB may still run (RG-Q11); **`prepare_review_after_index`**: skip `create_review_run` when not authoritative; **`reconcile_tasks`**: skip enqueue **before commit** when superseded; on supersede moment: `finalize_pipeline_github_check_neutral` for superseded in-flight pipelines (review **and** index); `@revy review` supersedes autostart on same revision; **`apply_resolution_status_for_synchronize`** runs in background task `apply_resolution_for_synchronize` (not inline on webhook — RG-15): non-coalesce index `enqueue_index_job` only after resolution `applied`; coalesce autostart scheduled after resolution with `coalesce_schedule_at` from synchronize; manual bypasses coalesce (P4). PRODUCT_PATTERNS row → **shipped** ([PR #54](https://github.com/raimondskrauklis/revy/pull/54); restart hotfix [PR #89](https://github.com/raimondskrauklis/revy/pull/89)).

**Scope — out:** Hard Celery revoke; judge changes.

**Deliverables:** Test — H2 before H1 index task runs → no H1 G10 `in_progress`; H2 before H1 publish → no H1 GitHub output; trace shows superseded.

**Depends on:** P1.

---

## P3 — Full surface flush (RG-3, RG-Q7)

**Goal:** No GitHub spill on any channel — one atomic flush at publish end for authoritative generation.

**Scope — in:** Refactor `run_publish_job`: build check summary, issue comment, resolve (Option A), inline posts **in memory**; single GitHub write sequence at end; no `_checkpoint_publish_surface` mid-pass; G10 `in_progress` until flush (authoritative gen only).

**Scope — out:** GitHub multi-comment review API (RG-Q5 defer).

**Deliverables:** Tests — no GitHub API between flush start and end.

**Depends on:** P2.

---

## P4 — Autostart coalesce (RG-4)

**Goal:** Absorb amend+push without two full LLM runs — **≤10 s** after last `synchronize` before autostart pipeline starts.

**Scope — in:** Debounced Celery task with `apply_async(countdown=…)` anchored to **`coalesce_schedule_at`** (synchronize time + `review_coalesce_seconds`); resolution runs first; autostart `maybe_enqueue` only after resolution `applied`; stale task no-ops via `is_authoritative_for_pull_request_head` (**v1:** no `celery_task_id` column / no Redis); cap `review_coalesce_seconds` at 10; default **0**; `@revy review` + manual index bypass.

**Scope — out:** Coalesce on command path; Redis unless Celery insufficient.

**Deliverables:** Test — two syncs within 5 s → one pipeline start; stale token discarded.

**Depends on:** P2.

---

## P5 — Trace, dogfood, judge gate, doc sync (RG-5, RG-6, RG-13)

**Goal:** Authoritative generation visible in trace; judge-candidates never publish without outcome; PR #53-class staging dogfood.

**Scope — in:** Trace manifest: `generation_superseded_at`, `publish_skipped_not_head`; **RG-6:** filter publish set — candidates require judge outcome row or judge-resolved group; log `judge_candidate_unpublished_missing_outcome`; **RG-13:** if any candidate lacks outcome at judge end → `judge_status` not `completed` (e.g. `skipped_unavailable`); investigate `not_applicable` when staging had candidates; dogfood two pushes ~8 s apart (**inline thread count**, not summary rows — §3c); PRODUCT_PATTERNS → **shipped**.

**Scope — out:** Frontend pipeline tab; block whole publish on judge.

**Deliverables:** Dogfood log; no escalation inline without outcome.

**Depends on:** P3 (P4 optional in gate notes).

---

## Parking lot

| Item |
|------|
| Hard Celery cancel mid-LLM |
| GitHub batch review API |
| Unify summary vs inline scope (pre-existing §3c) |

---

**Open item**

None — RG-Q5 locked; `review_coalesce_seconds` default **0** locked in execution index.

**Next step:** `phase-execution` from [REVIEW_GENERATION_LIFECYCLE_EXECUTION.md](./REVIEW_GENERATION_LIFECYCLE_EXECUTION.md) P0.
