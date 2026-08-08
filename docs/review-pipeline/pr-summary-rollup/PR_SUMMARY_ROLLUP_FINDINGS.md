# PR summary rollup — findings

**Date:** 2026-08-08  
**Purpose:** Baseline for **PR lifetime + this-push** summary metrics on GitHub surfaces, with **persisted rollup** from day one (Option 3). **No execution steps.**

**Trigger:** SOS-5 ([#84](https://github.com/raimondskrauklis/revy/pull/84), merged `2d7462b`) aligned `still_open` display with filtered block 2, but resolution story remains **per-push** (`### Resolution metrics (this push)`); authors lack a single **entire PR** rollup comparable to Greptile footer / CodeRabbit timeline clarity.

**Evidence:** Code on `main` post-#84; staging DB (13× `Moonshot review response truncated` pre-fix); kp-platform #489/#491 dogfood ([SOS findings](../still-open-summary-dogfood/STILL_OPEN_SUMMARY_DOGFOOD_FINDINGS.md)); [architecture peer review pass 1](./reviews/architecture-peer-review/pass-01-2026-08-08.md).

---

## Build principles

1. **Two horizons, one comment** — PR lifetime and this-push delta are **separate labeled sections**; never mix denominators (FR-Q12 stays push-pair; lifetime rate is its own formula).
2. **Display = table** — rollup `still_open_display` equals **full** `### Still open on PR` row count after `filter_pr_active_groups_for_summary` (SOS-D1/D7). Not the prior-only push metric.
3. **Persist at publish** — compute rollup each publish, write to `summary_json` **and** PR row; no “compute-only first” path.
4. **Lifetime = full DB on PR** — first post-deploy publish on a legacy PR includes all non-superseded groups in lifetime raised/resolved (PSR-Q9). No backfill/re-publish of old PRs (PSR-Q6). When `review_count == 1` and pre-existing groups exist, show disclosure footer (PSR-Q9).
5. **Reuse, don’t fork** — dedicated `github_pr_resolution_rollup.py` for lifetime math; formatter owns markdown; push-pair math stays in `github_resolution_metrics`.
6. **Verify against code** — cite `file:line`; dogfood script reads persisted keys.

---

## Terminology

| Term | Meaning |
|------|---------|
| **PR rollup** | Lifetime metrics on a pull request: raised, resolved (by method), still open (display), lifetime resolution rate |
| **Push manifest** | Existing reconcile `resolution_pass` / `format_resolution_metrics_block` — **this push pair only** (FR-Q12) |
| **`still_open_display`** | `len(_active_groups(verdict_groups(ctx)))` after summary filters — **full block 2 row count** |
| **`still_open_prior`** | `display_still_open_prior_count()` — prior-revision actives only; **push/G9 metric**, not rollup |
| **`pr_resolution_rollup`** | Persisted JSON object on publish job + PR latest snapshot |
| **Review count** | **Completed publish jobs** on PR (PSR-Q2) — dedicated count query, not inline-thread reuse fetch |

---

## What exists vs genuinely new

### Shipped (verified)

| Capability | Location | Notes |
|------------|----------|-------|
| Two-block tables | `format_summary_comment` `github_publish_formatter.py:663–691` | This generation + Still open on PR |
| PR-wide verdict | `verdict_groups`, `compute_publish_confidence` `github_publish_formatter.py:145–341` | Confidence/merge use filtered PR actives |
| Push resolution manifest | `build_resolution_pass_manifest` `github_resolution_metrics.py:697+` | FR-Q12 transitions-only |
| Push metrics block | `format_resolution_metrics_block` `github_publish_formatter.py:197–254` | Title: "this push"; `display_still_open_prior` override (SOS-D8) |
| G9 prose | `_g9_resolution_prose_for_ctx` `github_publish_formatter.py:409–416` | "Since last push" |
| `summary_json` per publish | `_build_summary_json` `github_publish_formatter.py:1193–1209` | `pr_active_count` uses filtered `verdict_groups` (1205–1207) |
| Display filters | `filter_pr_active_groups_for_summary` `github_publish_formatter.py:431+` | Collapsed + never-inlined orphans |
| Collapse refresh mid-flush | `apply_publish_summary_thread_collapse` `github_publish_formatter.py:598–640` | Rebuilds `summary_json` after inline collapse |
| Pipeline trace read | `get_resolution_metrics_for_review_run` `github_pipeline_trace.py:525–542` | Push manifest only |
| Dogfood script | `revy_review_dogfood_staging_validation.py` | Reads `summary_json`, not rollup |

### Genuinely new (this program)

| Capability | Why new |
|------------|---------|
| **`pr_resolution_rollup` manifest** | No lifetime aggregate today |
| **`_load_pr_groups_for_rollup`** | `_load_pr_active_groups` is active-only (`github_publish.py:1313–1325`) |
| **PR summary markdown block** | `### PR summary` above push delta |
| **PR row persistence** | `github_pull_requests` has no rollup column |
| **Post-collapse rollup compute** | Rollup must run with same ctx as final `summary_json` (pass-01 critical) |
| **Check-run push parity** | Check omits "Since last push" and resolution metrics |
| **Review metadata footer** | No review count / last-reviewed commit in comment |
| **Moonshot PR summary splice** | `splice_deterministic_pr_summary_block` (beyond findings-table splice) |
| **Rollup-aware dogfood gates** | Assert `still_open_display` vs block-2 parity |

### Reuse traps

| Trap | Detail |
|------|--------|
| **Lifetime rate ≠ FR-Q12** | Do not reuse `resolution_rate_pct` from push manifest for PR lifetime |
| **`still_open_display` ≠ `still_open_prior`** | Prior count excludes generation fingerprints — push/G9 only |
| **`pr_active_count` alias** | Today equals filtered block 2 count — do not conflate with rollup field names in tests |
| **Resolved superseded groups** | Lifetime `raised_count` excludes `state=superseded` |
| **`_load_pr_active_groups` for lifetime** | Active-only — use `_load_pr_groups_for_rollup` for raised/resolved |
| **Hygiene closures** | Include in resolved breakdown; `path_removed` in `resolved_by_method` |
| **Moonshot drift** | Splice deterministic PR summary block like findings tables |
| **Failed publish partial `summary_json`** | Rollup + PR row write only when publish reaches `completed` (PSR-Q5) |
| **`review_count` query** | Do not reuse `_fetch_prior_reusable_publish_jobs` (includes failed for inline reuse) |

---

## Catalog — target user-facing layout

Issue comment order (top → bottom):

| # | Section | Horizon | Source |
|---|---------|---------|--------|
| 1 | Narrative + merge + confidence | PR-wide | existing |
| 2 | `### PR summary` | **Lifetime** | **new** `format_pr_resolution_rollup_block` |
| 3 | `**Since last push:**` | This push | existing G9 (`still_open_prior`) |
| 4 | `### Resolution metrics (this push)` | This push | existing FR-Q12 block |
| 5 | Files needing attention | PR-wide | existing |
| 6 | `### This generation` / `### Still open on PR` | Both | existing |
| 7 | Details + **Review metadata** | Meta | reviews (N), revision, head_sha; lifetime disclosure when PSR-Q9 |

Check run (compact): confidence + **one-line PR rollup** + **one-line push delta** + two-block tables.

---

## `pr_resolution_rollup` manifest (contract v1)

Persisted on **`github_publish_jobs.summary_json.pr_resolution_rollup`** and **`github_pull_requests.pr_resolution_rollup`** (latest).

| Field | Type | Meaning |
|-------|------|---------|
| `schema_version` | int | `1` |
| `computed_at_revision_id` | uuid | Revision when rollup was computed |
| `revision_number` | int | Human revision |
| `review_count` | int | Completed publish jobs on PR (PSR-Q2) |
| `raised_count` | int | Non-superseded groups on PR |
| `resolved_count` | int | `state=resolved` on PR |
| `resolved_by_method` | object | `absent_and_addressed`, `judge_dismissed`, `verification_dismissed`, `human_dismissed`, `path_removed` |
| `still_open_display` | int | Full block 2 row count after filters |
| `still_open_generation` | int | Active in this generation only |
| `still_open_prior` | int | Prior-revision actives (push/G9 parity) |
| `lifetime_resolution_rate_pct` | float | `resolved / (resolved + still_open_display)` or N/A |
| `filter_snapshot` | object | Audit counts — keys locked PSR-Q10 |
| `push_manifest_ref` | object | `revision_number`, `transition_count` — pointer only |
| `lifetime_disclosure` | string \| null | PSR-Q9 footer when first publish on legacy PR |

### `filter_snapshot` v1 keys (PSR-Q10)

| Key | Meaning |
|-----|---------|
| `raw_active_before_filters` | Active groups before summary filters |
| `collapsed_hidden` | Omitted due to collapsed inline threads |
| `orphan_never_inlined_hidden` | Omitted never-inlined orphans |
| `compare_failed_hidden` | Active but hidden by compare-failed / closure-blocked display rules |

**Not in v1 schema:** time-series history array (future API).

---

## Implementation locks (pass-01)

| Lock | Rule |
|------|------|
| **Compute call sites** | `build_pr_resolution_rollup()` from `apply_publish_summary_thread_collapse` return path **and** final flush before `job.status = completed` — same filtered `PublishFormatContext` as published comment |
| **Group loader** | `_load_pr_groups_for_rollup(session, pull_request_id)` — `state != superseded` |
| **Review count** | `SELECT count(*) … WHERE pull_request_id = ? AND status = completed` |
| **PR row write** | Atomic with successful publish completion only |

---

## External research — adopt / defer / reject

| Pattern | Source | Decision |
|---------|--------|----------|
| Review counter + last commit in footer | Greptile | **Adopt** (metadata footer) |
| Summary regenerated every push | CodeRabbit | **Adopt** (already true — in-place comment) |
| Separate snapshot UI for history | CodeRabbit Change Stack | **Defer** |
| Analytics dashboard | Greptile org analytics | **Defer** |

---

## Data scope & exclusions

| Universe | Included | Excluded |
|----------|----------|----------|
| Lifetime raised | All `github_finding_groups` on PR where `state != superseded` | Superseded groups |
| Lifetime resolved | `state=resolved` on PR | — |
| Still open (display) | Filtered active groups in block 2 (`still_open_display`) | Collapsed, never-inlined orphans |
| Push metrics | Unchanged FR-Q12 cohort | — |
| Backfill | — | No re-publish of pre-program PRs (PSR-Q6) |

---

## Edge cases

| Case | Handling |
|------|----------|
| Revision 1 | PR summary: raised = generation count; push delta "first review" |
| Legacy PR, first post-deploy publish | Full DB lifetime counts (PSR-Q9); `lifetime_disclosure` in footer |
| All inline collapsed + clean generation | `still_open_display=0` |
| Compare-failed groups | `filter_snapshot.compare_failed_hidden` |
| Inline collapse mid-flush | Recompute rollup in `apply_publish_summary_thread_collapse` path |
| Publish retry after failed job | Rollup + PR row only on `completed` |
| Moonshot fallback | Deterministic PR summary splice |
| Merged/closed PR | Last publish rollup frozen on PR row |

---

## Decisions registry

| ID | Question | Status | Resolution |
|----|----------|--------|------------|
| PSR-Q1 | Ship compute-only before migration? | **locked** | **No** — persist on job + PR row from first deploy |
| PSR-Q2 | `review_count` definition | **locked** | **Completed publish jobs** on PR |
| PSR-Q3 | PR table column | **locked** | `github_pull_requests.pr_resolution_rollup` JSONB + job `summary_json` |
| PSR-Q4 | Lifetime rate formula | **locked** | `resolved / (resolved + still_open_display)` when denominator > 0; else N/A |
| PSR-Q5 | Failed publish partial rollup | **locked** | Write only when publish reaches `completed` |
| PSR-Q6 | Pre-program PR backfill | **locked** | **No** re-publish of old PRs (SOS-D4 extended) |
| PSR-Q7 | i18n for GitHub markdown | **locked** | EN only in formatter |
| PSR-Q8 | API exposure | **locked** | P1 spike: confirm routes; **P2 ship** `pr_resolution_rollup` on `GitHubPublishJobResponse` (or dedicated read) |
| PSR-Q9 | Legacy PR first publish lifetime scope | **locked** | **Full DB** non-superseded groups; disclosure footer when `review_count == 1` and pre-existing groups |
| PSR-Q10 | `filter_snapshot` v1 keys | **locked** | See table above |

---

## Parking lot

- Time-series rollup per revision for Revy UI sparkline
- Org-level analytics export (Greptile-style)
- `compute_check_conclusion` PR-wide alignment (separate program)
- Pipeline trace `rollup_pass` artifact on publish step (optional P2)

---

## Devil's advocate

- **Two rate columns confuse authors** — explicit "(lifetime)" vs "(this push)" headings.
- **Persisted rollup drifts from DB** — recompute every publish from groups + same filters.
- **Legacy PR full history surprises authors** — PSR-Q9 disclosure footer mitigates.

---

## Experiment / verification

| Gate | Pass criteria |
|------|----------------|
| Unit | `rollup.still_open_display == len(block 2 rows)` after filters |
| Unit | `rollup.still_open_prior == display_still_open_prior_count(ctx)` |
| Unit | Lifetime rate matches hand-count on fixture PR |
| Unit | Post-collapse flush reproduces same rollup as published comment |
| Staging dogfood | Multi-revision PR: PR summary + push block on rev ≥2; PR row matches comment |
| Script | `revy_review_dogfood_staging_validation.py` asserts `pr_resolution_rollup` keys |

---

## References

| Area | Path |
|------|------|
| Formatter | `backend/app/services/github_publish_formatter.py` |
| Resolution metrics (push) | `backend/app/services/github_resolution_metrics.py` |
| Rollup (new) | `backend/app/services/github_pr_resolution_rollup.py` (planned) |
| Publish surface | `backend/app/services/github_publish.py` |
| API schema | `backend/app/schemas/github_publish.py` |
| Peer review | `docs/review-pipeline/pr-summary-rollup/reviews/architecture-peer-review/pass-01-2026-08-08.md` |
