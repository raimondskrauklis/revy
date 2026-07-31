# Backend scripts runbook

Operator commands for staging validation scripts in `backend/scripts/`.

## Staging metrics (`judge_json_contract_staging_metrics.py`)

Judge JSON contract + review engineering context aggregates against the staging database.

Requires `PRODUCTION_DATABASE_URL` in `backend/.env` (revy-staging). Use `DATABASE_SSL_INSECURE=1` when connecting to managed Postgres with certificate issues.

**Invocation:** always wrap script calls in `pipenv run sh -c '...'` from `backend/` so `.env` loads and quoting stays correct.

```bash
cd backend

# Full history (baseline calibration only — not for RCX sign-off)
DATABASE_SSL_INSECURE=1 pipenv run sh -c 'python -m scripts.judge_json_contract_staging_metrics'

# Post-deploy window (RCX sign-off)
DATABASE_SSL_INSECURE=1 pipenv run sh -c \
  'python -m scripts.judge_json_contract_staging_metrics --since <deploy-iso> --json'

# RCX pass/fail gate (use with --since for P8 sign-off)
DATABASE_SSL_INSECURE=1 pipenv run sh -c \
  'python -m scripts.judge_json_contract_staging_metrics --since <deploy-iso> --rcx-gate'

# Machine-readable gate + metrics
DATABASE_SSL_INSECURE=1 pipenv run sh -c \
  'python -m scripts.judge_json_contract_staging_metrics --since <deploy-iso> --rcx-gate --json'
```

**RCX gate:** Primary source is `github_review_runs.context_stats`; retrieve manifest `engineering_context_injected` is cross-checked. Exit code **1** when any check is `FAIL` (`INCONCLUSIVE` does not fail the gate).

See [REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md](../review-pipeline/review-engineering-context/REVIEW_ENGINEERING_CONTEXT_STAGING_VALIDATION.md) and [JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md](../review-pipeline/judge-json-contract/JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md).

## RR-W1 dogfood gate (`revy_review_dogfood_staging_validation.py`)

Per-PR closure-loop validation on `raimondskrauklis/revy` staging dogfood PRs. Requires **≥5 completed review runs** and DB evidence for resolution/judge/publish parity.

```bash
cd backend

DATABASE_SSL_INSECURE=1 pipenv run sh -c \
  'python -m scripts.revy_review_dogfood_staging_validation --pr-number <N> --since 2026-07-31T19:08:32Z --json'

DATABASE_SSL_INSECURE=1 pipenv run sh -c \
  'python -m scripts.revy_review_dogfood_staging_validation --pr-number <N> --since 2026-07-31T19:08:32Z --rr-v-gate'
```

Exit code **1** when any RR-V check is `PENDING` or `FAIL`. See [REVY_REVIEW_DOGFOOD_STAGING_VALIDATION.md](../review-pipeline/revy-review-dogfood/REVY_REVIEW_DOGFOOD_STAGING_VALIDATION.md).
