# Still-open summary dogfood P1 — SOS-5 orphan filter + metrics (execution)

Phase **P1** of [STILL_OPEN_SUMMARY_DOGFOOD_GENERAL_PLAN.md](../STILL_OPEN_SUMMARY_DOGFOOD_GENERAL_PLAN.md). **P1 only.**

**Goal:** When all GitHub inline threads are collapsed and generation is clean, block 2, narrative, confidence, and G9 must not warn about summary-only orphans (never inlined).

**Evidence:** kp-platform [#491](https://github.com/raimondskrauklis/kp-platform/pull/491) rev 3 — `bdcf4d58` never in `github_inline_threads`; block 2 + G9 still showed 1 still open.

## Decisions locked for P1

- **SOS-D7** — `filter_pr_active_groups_for_summary` drops active groups not in `ever_inlined_fingerprints` when absent from generation publishable set.
- **SOS-D8** — G9 + resolution metrics block use `display_still_open_prior_count(ctx)` (filtered verdict, prior-only) instead of raw reconcile `still_open_count` for author-facing copy.
- **SOS-D4** unchanged — no backfill for pre-#83 PRs.

## Out of scope for P1

- Reconcile Pass 1 line-region changes (SOS-2)
- DB closure for orphans
- Pre-#83 PR repair

---

## P1.1 — `ever_inlined_fingerprints` loader

**What:** `_load_ever_inlined_fingerprints(prior_jobs, current_job_summary=…)` — union of fingerprints from publish `github_inline_threads` maps on prior jobs (completed **and failed** for inline-thread reuse) plus the **current** job summary when a retry checkpoints partial inlines. Collapsed-inline memory uses **completed** jobs only (see `_load_prior_collapsed_inline_fingerprints`).

**Files:** `backend/app/services/github_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish.py -k ever_inlined -q
```

---

## P1.2 — Summary orphan filter (SOS-5)

**What:** Extend `filter_pr_active_groups_for_summary` with `ever_inlined_fingerprints`; wire from `_build_publish_surface` and `apply_publish_summary_thread_collapse` via `PublishFormatContext.ever_inlined_fingerprints`.

**Files:** `backend/app/services/github_publish_formatter.py`, `backend/app/services/github_publish.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py -k "never_inlined or orphan" -q
```

---

## P1.3 — G9 + resolution metrics display alignment

**What:** `display_still_open_prior_count(ctx)`; pass to `format_resolution_metrics_block` and `build_g9_resolution_prose_from_manifest` as `display_still_open_prior`.

**Files:** `backend/app/services/github_publish_formatter.py`, `backend/tests/unit/test_github_publish_formatter.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_publish_formatter.py -k "display_still_open or clean_generation" -q
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run pytest tests/unit/test_github_publish_formatter.py tests/unit/test_github_publish.py -q
pipenv run ruff check app/services/github_publish_formatter.py app/services/github_publish.py
```

**Dogfood gate (post-deploy):** kp-platform #491 `@revy review` on clean generation → block 2 empty table body; G9 without “still open from prior review”; confidence 5/5 when no display actives.

**Next:** [STILL_OPEN_SUMMARY_DOGFOOD_P2_EXECUTION.md](./STILL_OPEN_SUMMARY_DOGFOOD_P2_EXECUTION.md) — doc sync + sign-off.
