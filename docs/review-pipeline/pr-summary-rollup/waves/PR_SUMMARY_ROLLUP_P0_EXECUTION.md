# docs/review-pipeline/pr-summary-rollup/waves/PR_SUMMARY_ROLLUP_P0_EXECUTION.md

# P0 — Rollup contract, migration, compute, persist (execution)

Phase **P0** of [`PR_SUMMARY_ROLLUP_GENERAL_PLAN.md`](../PR_SUMMARY_ROLLUP_GENERAL_PLAN.md). Baseline: [`PR_SUMMARY_ROLLUP_FINDINGS.md`](../PR_SUMMARY_ROLLUP_FINDINGS.md) §manifest, implementation locks, PSR-Q1–Q7. **P0 only.**

**Goal:** Authoritative `pr_resolution_rollup` computed at correct flush points and stored on job `summary_json` + `github_pull_requests.pr_resolution_rollup`.

## Decisions locked for P0

- Manifest v1 fields per findings §`pr_resolution_rollup` — `schema_version=1`, `filter_snapshot` keys PSR-Q10, `lifetime_resolution_rate_pct` = `resolved / (resolved + still_open_display)` when denominator > 0 else `null`.
- `still_open_display` = `len(_active_groups(verdict_groups(ctx)))` after `filter_pr_active_groups_for_summary` — **not** `display_still_open_prior_count()`.
- `still_open_prior` in manifest = `display_still_open_prior_count(ctx)` for push/G9 parity only.
- `resolved_by_method` buckets: `absent_and_addressed`, `judge_dismissed`, `verification_dismissed`, `human_dismissed`, `path_removed` (hygiene path-removed closures via `_is_hygiene_path_removed_closure` pattern from `github_resolution_metrics.py`).
- `build_pr_resolution_rollup(ctx, all_pr_groups, review_count)` in **`github_pr_resolution_rollup.py`** — lifetime math only; push manifest stays in `github_resolution_metrics`.
- `_load_pr_groups_for_rollup(session, pull_request_id)` — `state != superseded` (not `_load_pr_active_groups`).
- `count_completed_publish_jobs(session, pull_request_id)` — dedicated query; **do not** reuse `_fetch_prior_reusable_publish_jobs`.
- Compute with same filtered `PublishFormatContext` as published comment — call sites: `apply_publish_summary_thread_collapse` return path **and** `_flush_publish_surface` final merge before `job.status = completed` (pass-01 critical).
- PR row JSONB write atomic with successful publish completion only (PSR-Q5); no rollup on failed/partial jobs.
- PSR-Q9 lifetime counts: first publish on legacy PR includes full DB non-superseded groups; set `lifetime_disclosure` when `review_count == 1` and `raised_count > len(ctx.groups)`.

## PR review context (first commit) — **hard gate**

- **SSOT:** `.revy/review-context.json` — `active_program: "pr-summary-rollup"`; `programs[]` = **one entry only** (remove prior programs on switch); `scope: ["backend/**"]`; three doc paths below.
- **Greptile:** regenerate `.greptile/files.json` from SSOT — **do not hand-edit**.
- **Bugbot:** `.cursor/BUGBOT.md` — active program PSR + links to execution, findings, general plan.

**Doc paths (SSOT `paths[]` only):**

- `docs/review-pipeline/pr-summary-rollup/waves/PR_SUMMARY_ROLLUP_EXECUTION.md`
- `docs/review-pipeline/pr-summary-rollup/PR_SUMMARY_ROLLUP_FINDINGS.md`
- `docs/review-pipeline/pr-summary-rollup/PR_SUMMARY_ROLLUP_GENERAL_PLAN.md`

## Out of scope for P0 (later phases)

- Markdown `### PR summary` block, section reorder, check-run one-liners → **P1**
- Moonshot prompt / splice, API response field, dogfood gates → **P2**
- Staging validation memo / sign-off → **P3**

---

## P0.0 — Program PR review context (SSOT + Greptile + Bugbot)

**What:** Switch SSOT `active_program` to `pr-summary-rollup`; add PSR program entry; regenerate Greptile `files.json`; update Bugbot active program block.

**Files:** `.revy/review-context.json`, `.greptile/files.json`, `.cursor/BUGBOT.md`

**Deliverable:**

```bash
cd backend && python -m scripts.generate_greptile_files_from_review_context --write
python -m scripts.generate_greptile_files_from_review_context --check
pipenv run pytest tests/unit/test_generate_greptile_files.py -q
python -m json.tool ../.revy/review-context.json > /dev/null
```

---

## P0.1 — Alembic migration `pr_resolution_rollup` JSONB

**What:** Hand-written revision `0030_github_pull_request_pr_resolution_rollup.py` — add nullable `pr_resolution_rollup` JSONB column on `github_pull_requests`. Update `GitHubPullRequestORM`.

**Files:** `backend/alembic/versions/2026_08_08_1000_0030_github_pull_request_pr_resolution_rollup.py`, `backend/app/models/github_pull_request.py`

**Deliverable:** revision applies cleanly; ORM field present.

```bash
cd backend && pipenv run ruff check app/models/github_pull_request.py
```

**LOOP pause:** agent stops after this subphase for human migration review before continuing P0.2.

---

## P0.2 — `github_pr_resolution_rollup.py` module

**What:** New module with `build_pr_resolution_rollup()`, `count_completed_publish_jobs()`, manifest builders for `filter_snapshot` (PSR-Q10 keys), `resolved_by_method`, `push_manifest_ref` pointer from ctx. Export typed dict / Pydantic model for manifest v1.

**Files:** `backend/app/services/github_pr_resolution_rollup.py`

**Deliverable:**

```bash
cd backend && pipenv run ruff check app/services/github_pr_resolution_rollup.py
```

---

## P0.3 — `_load_pr_groups_for_rollup` loader

**What:** Add `async def _load_pr_groups_for_rollup(session, *, pull_request_id) -> list[GitHubFindingGroupORM]` selecting all groups where `state != superseded`. Wire into rollup builder call sites (not for active-only paths).

**Files:** `backend/app/services/github_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run ruff check app/services/github_publish.py
```

---

## P0.4 — Wire compute + persist at flush points

**What:** Helper `_attach_pr_resolution_rollup(session, job, pull_request, ctx, all_pr_groups)` — compute manifest, merge into `job.summary_json["pr_resolution_rollup"]`, set `pull_request.pr_resolution_rollup`. **Authoritative final compute** in `_flush_publish_surface` using post-collapse ctx when `apply_publish_summary_thread_collapse` ran (use `filtered_ctx` / collapsed `summary_json` inputs). Also refresh rollup inside `apply_publish_summary_thread_collapse` return so mid-flush `summary_json` stays consistent before GitHub write. When no collapse, compute once in flush from `build.format_ctx`. No PR row / rollup write when publish aborts before `completed`.

**Files:** `backend/app/services/github_publish.py`, `backend/app/services/github_publish_formatter.py` (`apply_publish_summary_thread_collapse`)

**Deliverable:**

```bash
cd backend && pipenv run ruff check app/services/github_publish.py app/services/github_publish_formatter.py
```

---

## P0.5 — Unit tests (manifest + post-collapse parity)

**What:** New `test_github_pr_resolution_rollup.py` — rev 1, collapsed hidden in `filter_snapshot`, resolved mix + `path_removed`, `still_open_display` vs block-2 row count, `still_open_prior` vs `display_still_open_prior_count`, lifetime rate hand-count, legacy PR PSR-Q9 disclosure, post-collapse parity (rollup after `apply_publish_summary_thread_collapse` matches pre-publish filtered ctx). Extend `test_github_publish.py` for persist-on-completed-only and PR row write.

**Files:** `backend/tests/unit/test_github_pr_resolution_rollup.py`, `backend/tests/unit/test_github_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_pr_resolution_rollup.py tests/unit/test_github_publish.py -k "rollup or pr_resolution" -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_pr_resolution_rollup.py tests/unit/test_github_publish.py tests/unit/test_generate_greptile_files.py -k "rollup or pr_resolution" -q
pipenv run ruff check app/services/github_pr_resolution_rollup.py app/services/github_publish.py app/services/github_publish_formatter.py app/models/github_pull_request.py
```

**Deploy:** ship migration before workers read PR row column.

**Next:** [`PR_SUMMARY_ROLLUP_P1_EXECUTION.md`](./PR_SUMMARY_ROLLUP_P1_EXECUTION.md)
