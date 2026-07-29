# Review engineering context — staging validation

**Program:** [README.md](./README.md) · **Baseline:** [REVIEW_ENGINEERING_CONTEXT_FINDINGS.md](./REVIEW_ENGINEERING_CONTEXT_FINDINGS.md)

**Status:** P0–P4 on `main` (#60) deployed · **Pass 1 filled** (2026-07-29) · Pass 2 after PR #61 merge.

## Deploy

| Item | Status |
|------|--------|
| `main` merged (#60) | done (`84ab03f`) |
| Alembic `0029_review_context_stats` | done on staging |
| Worker + API deploy | done (2026-07-29, workflow `30426495254`) |
| Post-deploy scoped review run | **done** — 2 runs (PR #61 dogfood, pre-P6 worker) |

**`--since` window (pass 1):** `2026-07-29T05:55:00Z` (#60 deploy)

## Dogfood trigger steps

1. ~~Merge P6+P7 PR to staging~~ — pass 1 used #60 worker on PR #61 autostart (valid for inject/caps).
2. Confirm autostart review **or** PR comment `@revy review` on latest `head_sha`.
3. Confirm `revy/review` check completes.
4. Run metrics:
   ```bash
   cd backend
   DATABASE_SSL_INSECURE=1 pipenv run sh -c \
     'python -m scripts.judge_json_contract_staging_metrics --since 2026-07-29T05:55:00Z --rcx-gate --json' \
     | tee /tmp/rcx-pass1.json
   ```
5. Fill post-deploy tables below; operator sign-off when all gates pass.

**Pass 2:** After PR #61 merge + deploy — new `--since` ISO, re-run script, refresh publish surface + API rows.

## Latest review runs (pass 1 window)

| `review_run_id` | `created_at` (UTC) | PR / trigger | `engineering_context_injected` | Notes |
|-----------------|-------------------|--------------|------------------------------|-------|
| `019faca7-8d1a-72cb-b982-48c5710b9f24` | 2026-07-29 06:54:49 | PR #61 rev 1 (`5ab8b10`) | true | First post-#60 dogfood |
| `019facbd-d7a7-775e-9380-3ef48ca87e68` | 2026-07-29 07:19:10 | PR #61 rev 2 (`4edb107`) | true | Latest run |

**Latest run `context_stats` sample** (`019facbd-d7a7-775e-9380-3ef48ca87e68`):

```json
{
  "active_program": "review-engineering-context",
  "diff_max_bytes": 524288,
  "unified_diff_bytes": 126680,
  "diff_truncated": false,
  "omitted_files_count": 0,
  "omitted_md_count": 0,
  "engineering_context_injected": true,
  "engineering_context_bytes": 4426,
  "engineering_context_deduped_paths": [
    "docs/review-pipeline/review-engineering-context/waves/REVIEW_ENGINEERING_CONTEXT_EXECUTION.md",
    "docs/review-pipeline/review-engineering-context/REVIEW_ENGINEERING_CONTEXT_FINDINGS.md",
    "docs/review-pipeline/review-engineering-context/REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md"
  ],
  "lock_ids_extracted": ["RCX-D1", "…", "RCX-D17"],
  "engineering_context_errors": [],
  "prompt_chars": 162553
}
```

## Metrics — pre-RCX baseline (2026-07-29)

**Queried:** full staging history pre-RCX deploy · 40 completed runs · see findings § Validation metrics.

| Metric | Baseline | Target (post-RCX) | Post-deploy (pass 1) |
|--------|----------|-------------------|----------------------|
| Diff truncated % | 25.0% | < 5% (≥3 runs in window) | **0.0%** (2 runs — INCONCLUSIVE) |
| Omitted `.md` runs | 9 / 40 | 0 | **0** |
| `engineering_context_injected` scoped runs | 0 (pre-RCX) | 100% scoped | **2/2** |
| Prompt p50 / p95 chars | ~143k / ~164k | stable / lower omit rate | **156,115 / 161,909** |
| Judge lock block on escalation | no (pre-RCX) | yes when candidates | N/A (0 escalation candidates) |

**Script:** `judge_json_contract_staging_metrics.py --since 2026-07-29T05:55:00Z --rcx-gate` → **overall PASS** (2026-07-29).

## `context_stats` aggregates (post-deploy)

| Field | Target | Post-deploy (pass 1) |
|-------|--------|----------------------|
| `engineering_context_injected` | true on scoped runs | **true** (2/2) |
| `engineering_context_bytes` | > 0 | **4426** (p50) |
| `lock_ids_extracted` | non-empty on program PR | **RCX-D1…D17** (17 locks) |
| `diff_max_bytes` | 524288 | **524288** |
| `unified_diff_bytes` | populated | **126,680** (latest run) |
| `engineering_context_deduped_paths` | informational | **3** MD paths deduped vs diff |
| `engineering_context_errors` | empty on success | **[]** |

## Publish surface (P6)

| Check | Post-deploy |
|-------|-------------|
| revybot issue comment Greptile-depth narrative | **pass 2** — pre-P6 worker on pass 1 runs |
| Fallback parity when Moonshot disabled/fails (RCX-D14) | **pass 2** — after PR #61 deploy |

## Operator API (P7)

| Check | Post-deploy |
|-------|-------------|
| `GET` review run includes `context_stats` | **pass 2** — API field on PR #61 branch only |
| Metrics script `--rcx-gate` PASS | **PASS** (pass 1, local script on branch) |

## Sign-off

| Gate | Owner | Status |
|------|-------|--------|
| Post-#60 dogfood PR + review run | operator | **done** (PR #61, 2 runs) |
| Pass 1 metrics filled (`--since` + `--rcx-gate`) | operator | **done** (2026-07-29) |
| RCX inject + caps (`engineering_context_*`, omitted md, truncate) | operator | **PASS** |
| Greptile-depth issue comment on dogfood PR | operator | **pass 2** (pending #61 deploy) |
| `GET context_stats` API spot-check | operator | **pass 2** |
| Contradict locks % on dogfood findings | operator | pending (target 0%) |
| Judge `--since` re-validation (RCX-G14) | operator | pending (0 judge candidates in window) |

**Operator sign-off (pass 1 — RCX inject/caps):** _2026-07-29 — inject, caps, `context_stats` column, `--rcx-gate` PASS on 2-run window. Publish surface + API deferred to pass 2 after PR #61._
