# Judge JSON contract — staging validation

**Purpose:** Human gate for program closeout (P5). Fill after deploy to `revy-staging`.

**Baseline:** [JUDGE_JSON_CONTRACT_FINDINGS.md](./JUDGE_JSON_CONTRACT_FINDINGS.md) — 13/15 judge manifest candidates failed parse (2026-07-28).

**Metrics script:** `backend/scripts/judge_json_contract_staging_metrics.py` — [BACKEND_SCRIPTS_RUNBOOK.md](../../utils/BACKEND_SCRIPTS_RUNBOOK.md)

---

## Deploy status

| Item | Value |
|------|-------|
| Merged to `main` | `9a7b5cb` (#58, 2026-07-29) |
| Staging alembic | `2026_07_29_1200_0029_review_context_stats` (post-#60) |
| Judge-json-contract on staging worker | **deployed** (#58 on `main`) — post-#60 dogfood pending judge escalation run |

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

### Review context (Moonshot / RCX — same script)

**Queried:** 2026-07-29 · `revy-staging` · alembic `0028` · full history (pre-RCX). See [REVIEW_ENGINEERING_CONTEXT_FINDINGS.md](../review-engineering-context/REVIEW_ENGINEERING_CONTEXT_FINDINGS.md) § Validation metrics.

**Note:** `engineering_context_injected` is read from retrieve manifest **and** `github_review_runs.context_stats` (migration `0029`, RCX #60).

| Metric | Baseline (pre-RCX) | Target | Post-#60 (`--since 2026-07-29T05:55:00Z`) |
|--------|-------------------|--------|-------------------------------------------|
| Completed runs (retrieve manifest) | **40** | — | **2** |
| Diff truncated % | **25.0%** (10/40) | <5% | **0.0%** (INCONCLUSIVE — 2 runs) |
| Omitted files p50 / p95 | **0 / 4** | p95 ≤2 | **0 / 0** |
| Runs with omitted `.md` | **9** | 0 | **0** |
| Moonshot prompt p50 / p95 (chars) | **143,129 / 163,981** | p95 <400k | **156,115 / 161,909** ✓ |
| `engineering_context_injected` runs | **0** (pre-RCX) | 100% scoped | **2/2** ✓ |
| `context_stats` rows | **0** (pre-RCX) | each scoped run | **2** ✓ |
| `DIFF_MAX_BYTES` config | **128 KB** hardcoded | **512 KB** | **524288** ✓ |

**Post-#58 judge candidates in same window:** 0 — judge persistence not exercised; needs escalation dogfood PR.

### Judge contract (baseline)

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
| Outcome persistence % | — | — | 0 judge candidates in post-#60 window |
| `user_prompt` p50 | — | — | |
| `retry_count` > 0 on recoveries | — | — | |
| Sample `review_run_id` (RCX) | `019facbd-d7a7-775e-9380-3ef48ca87e68` | 2026-07-29 | PR #61 latest; inject ✓ |

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
