# Backend scripts runbook

Operator commands for staging validation scripts in `backend/scripts/`.

## Staging metrics (`judge_json_contract_staging_metrics.py`)

Judge JSON contract + review engineering context aggregates against the staging database.

Requires `PRODUCTION_DATABASE_URL` in `backend/.env` (revy-staging). Use `DATABASE_SSL_INSECURE=1` when connecting to managed Postgres with certificate issues.

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
