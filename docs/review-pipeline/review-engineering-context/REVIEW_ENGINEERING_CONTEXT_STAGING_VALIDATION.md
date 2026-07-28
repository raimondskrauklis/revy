# Review engineering context — staging validation

**Program:** [README.md](./README.md) · **Baseline:** [REVIEW_ENGINEERING_CONTEXT_FINDINGS.md](./REVIEW_ENGINEERING_CONTEXT_FINDINGS.md)

**Status:** Code shipped on branch `docs/judge-json-contract-staging-validation` — **human gate pending** (deploy + dogfood).

## Deploy

| Item | Status |
|------|--------|
| Branch merged to staging | pending |
| Alembic `0029_review_context_stats` | pending |
| Worker + API deploy | pending |

## Dogfood trigger steps

1. Deploy RCX branch to staging (alembic `0029`).
2. Open/merge dogfood PR with `backend/**` changes.
3. Trigger review: workspace autostart **or** PR comment `@revy review`.
4. Confirm `revy/review` check completes on latest `head_sha`.
5. Run metrics: `cd backend && DATABASE_SSL_INSECURE=1 pipenv run sh -c 'python -m scripts.judge_json_contract_staging_metrics --since <deploy-iso> --json'`

## Metrics — pre-RCX baseline (2026-07-29)

**Queried:** full staging history pre-RCX deploy · 40 completed runs · see findings § Validation metrics.

| Metric | Baseline | Target (post-RCX) | Post-deploy |
|--------|----------|-------------------|-------------|
| Diff truncated % | 25.0% | < 5% | |
| Omitted `.md` runs | 9 / 40 | 0 | |
| `engineering_context_injected` scoped runs | 0 (field absent) | 100% scoped | |
| Prompt p95 chars | ~164k | stable / lower omit rate | |
| Judge lock block on escalation | no | yes when candidates | |

## `context_stats` aggregates (post-deploy)

| Field | Target | Post-deploy |
|-------|--------|-------------|
| `engineering_context_injected` | true on scoped runs | |
| `engineering_context_bytes` | > 0 | |
| `lock_ids_extracted` | non-empty on program PR | |
| `diff_max_bytes` | 524288 | |
| `unified_diff_bytes` | populated | |

## Publish surface (P5.5)

| Check | Post-deploy |
|-------|-------------|
| revybot issue comment Greptile-depth narrative | pending P5.5 |

## Sign-off

| Gate | Owner | Status |
|------|-------|--------|
| P5.2 dogfood PR + review run | operator | pending |
| P5.3 metrics filled | operator | pending |
| P5.5 issue-comment narrative | operator | pending |
| Contradict locks % on dogfood findings | operator | pending (target 0%) |

**Operator sign-off:** _pending_
