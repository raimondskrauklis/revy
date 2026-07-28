# Judge JSON contract — staging validation

**Purpose:** Human gate for program closeout (P5). Fill after deploy to `revy-staging`.

**Baseline:** [JUDGE_JSON_CONTRACT_FINDINGS.md](./JUDGE_JSON_CONTRACT_FINDINGS.md) — 13/15 judge manifest candidates failed parse (2026-07-28).

**Metrics script:** `backend/scripts/judge_json_contract_staging_metrics.py` — [BACKEND_SCRIPTS_RUNBOOK.md](../../utils/BACKEND_SCRIPTS_RUNBOOK.md)

---

## Deploy status

| Item | Value |
|------|-------|
| Merged to `main` | `9a7b5cb` (#58, 2026-07-29) |
| Staging alembic | `2026_07_28_1200_0028_finding_resolution_closure` |
| Judge-json-contract on staging worker | **pending deploy** — manifests still lack `parse_error` / `retry_count` (pre-ship) |

**Operator:** deploy `main` to staging, trigger dogfood PR with escalation finding, re-run metrics script.

```bash
cd backend
DATABASE_SSL_INSECURE=1 pipenv run sh -c 'python -m scripts.judge_json_contract_staging_metrics'
DATABASE_SSL_INSECURE=1 pipenv run sh -c 'python -m scripts.judge_json_contract_staging_metrics --since 2026-07-29T00:00:00Z'
```

---

## P4 gate (operator — after P3 deploy)

| Check | Required | Result | Date |
|-------|----------|--------|------|
| P3 staging outcome persistence ≥95% | If yes → P4 doc-only skip | **pending deploy** | — |

---

## Success metrics

### Baseline (all staging history — pre #58 deploy)

**Queried:** 2026-07-29 · `revy-staging`

| Metric | Baseline | Target | After deploy |
|--------|----------|--------|--------------|
| Judge candidates → valid `outcome` in manifest | **21.1%** (4/19) | ≥95% | pending |
| Judge runs → any `github_finding_judge_outcomes` row | **35%** (7/20) | ≥95% | pending |
| Judge `user_prompt` p50 | **1,083** chars | ≤2k (snippet tier) | pending |
| `file_patch_chars` p50 | **0** (snippet tier when present) | null when snippet | pending |
| Manifest `parse_error` populated on failure | **0** (pre-G1 deploy) | all parse fails | pending |
| RG-6 `judge_candidate_unpublished_missing_outcome` | frequent on parse fail | rare | pending |

### Post-deploy (fill after dogfood run)

| Metric | Value | Date | Notes |
|--------|-------|------|-------|
| Outcome persistence % | — | — | |
| `user_prompt` p50 | — | — | |
| `retry_count` > 0 on recoveries | — | — | |
| Sample `review_run_id` | — | — | |

---

## P0 smoke matrix (final)

| Path | `--structured` | Result | Notes |
|------|----------------|--------|-------|
| RTU gateway | no | pass | plain JSON 240–10k chars |
| RTU gateway | yes | fail | `structured_outputs not supported in your workspace` |
| Direct API | — | n/a locally | `anthropic_direct_enabled=False` |

**P3 lock:** `REVY_JUDGE_STRUCTURED_OUTPUT=false` on RTU; `parse_llm_json_object` + snippet-first prompts primary.

**P4 note:** Retry code shipped in #58; skip rule applies only if post-deploy persistence ≥95% without retry benefit — evaluate after deploy.

---

## SQL repro

See [FINDING_RESOLUTION_TECHNICAL_FINDINGS.md](../finding-resolution/FINDING_RESOLUTION_TECHNICAL_FINDINGS.md). Prefer the metrics script for aggregates.

---

## Sign-off

| Role | Date | Outcome persistence % | Notes |
|------|------|----------------------|-------|
| Operator | — | — | pending deploy + dogfood PR |
