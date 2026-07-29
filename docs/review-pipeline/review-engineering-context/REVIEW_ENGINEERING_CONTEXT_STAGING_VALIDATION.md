# Review engineering context — staging validation

**Program:** [README.md](./README.md) · **Baseline:** [REVIEW_ENGINEERING_CONTEXT_FINDINGS.md](./REVIEW_ENGINEERING_CONTEXT_FINDINGS.md)

**Status:** P0–P4 on `main` (#60) deployed to staging · **P6–P8 human gate pending** (dogfood PR + sign-off).

## Deploy

| Item | Status |
|------|--------|
| `main` merged (#60) | done (`84ab03f`) |
| Alembic `0029_review_context_stats` | done on staging |
| Worker + API deploy | done (2026-07-29) |
| Post-deploy scoped review run | **pending** — requires P6+P7 dogfood PR |

## Dogfood trigger steps

1. Merge P6+P7 PR to staging (`backend/**` changes — RCX-D15).
2. Confirm autostart review **or** PR comment `@revy review` on latest `head_sha`.
3. Confirm `revy/review` check completes.
4. Run metrics:
   ```bash
   cd backend
   DATABASE_SSL_INSECURE=1 pipenv run sh -c \
     'python -m scripts.judge_json_contract_staging_metrics --since <deploy-iso> --rcx-gate --json'
   ```
5. Fill post-deploy tables below; operator sign-off when all gates pass.

## Metrics — pre-RCX baseline (2026-07-29)

**Queried:** full staging history pre-RCX deploy · 40 completed runs · see findings § Validation metrics.

| Metric | Baseline | Target (post-RCX) | Post-deploy |
|--------|----------|-------------------|-------------|
| Diff truncated % | 25.0% | < 5% (≥3 runs in window) | |
| Omitted `.md` runs | 9 / 40 | 0 | |
| `engineering_context_injected` scoped runs | 0 (pre-RCX) | 100% scoped | |
| Prompt p95 chars | ~164k | stable / lower omit rate | |
| Judge lock block on escalation | no (pre-RCX) | yes when candidates | |

## `context_stats` aggregates (post-deploy)

| Field | Target | Post-deploy |
|-------|--------|-------------|
| `engineering_context_injected` | true on scoped runs | |
| `engineering_context_bytes` | > 0 | |
| `lock_ids_extracted` | non-empty on program PR | |
| `diff_max_bytes` | 524288 | |
| `unified_diff_bytes` | populated | |

## Publish surface (P6)

| Check | Post-deploy |
|-------|-------------|
| revybot issue comment Greptile-depth narrative | pending P6 |
| Fallback parity when Moonshot disabled/fails (RCX-D14) | pending P6 |

## Operator API (P7)

| Check | Post-deploy |
|-------|-------------|
| `GET` review run includes `context_stats` | pending P7 |
| Metrics script `--rcx-gate` PASS | pending P7 |

## Sign-off

| Gate | Owner | Status |
|------|-------|--------|
| P6+P7 dogfood PR + review run | operator | pending |
| P8 metrics filled (`--since` + `--rcx-gate`) | operator | pending |
| Greptile-depth issue comment on dogfood PR | operator | pending |
| Contradict locks % on dogfood findings | operator | pending (target 0%) |
| Judge `--since` re-validation (RCX-G14) | operator | pending |

**Operator sign-off:** _pending_
