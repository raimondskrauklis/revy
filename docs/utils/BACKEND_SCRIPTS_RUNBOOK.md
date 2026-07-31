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

Per-PR closure-loop validation on `raimondskrauklis/revy` staging dogfood PRs. Requires **≥5 completed review runs** and DB evidence for resolution/judge/publish parity. Uses `STAGING_DATABASE_URL` when set (falls back to `DATABASE_URL`).

```bash
cd backend

# Example: PR #80 after RR-W1 deploy (deda3c9)
DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.revy_review_dogfood_staging_validation \
  --pr-number 80 --since 2026-07-31T19:08:32Z --json

DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.revy_review_dogfood_staging_validation \
  --pr-number 80 --since 2026-07-31T19:08:32Z --rr-v-gate
```

Exit code **1** when any RR-V check is `PENDING` or `FAIL` (RR-V5 manual pytest matrix reports `PENDING` by design). See [REVY_REVIEW_DOGFOOD_STAGING_VALIDATION.md](../review-pipeline/revy-review-dogfood/REVY_REVIEW_DOGFOOD_STAGING_VALIDATION.md).

## Judge staging spend (`judge_staging_spend_metrics.py`)

Reconcile Anthropic `revy-judge` billing vs staging DB judge manifests and pipeline step tokens.

```bash
cd backend

DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.judge_staging_spend_metrics \
  --since 2026-07-31T00:00:00Z

DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.judge_staging_spend_metrics \
  --since 2026-07-31T00:00:00Z --json
```

See [JUDGE_STAGING_SPEND_INVESTIGATION_FINDINGS.md](../review-pipeline/judge/JUDGE_STAGING_SPEND_INVESTIGATION_FINDINGS.md).

## Moonshot staging spend (`moonshot_staging_spend_metrics.py`)

Reconcile Moonshot request-log CSV (`revy-main` / `kimi-k2.7-code`) vs staging DB completed review runs.

```bash
cd backend

pipenv run python -m scripts.moonshot_staging_spend_metrics \
  --csv ../misc/request_log_part_0001.csv --days 3

DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.moonshot_staging_spend_metrics \
  --csv ../misc/request_log_part_0001.csv --since 2026-07-30T00:00:00Z --json
```

**RR-V4:** Gate checks **latest publish only** for `resolve_mutation_failed`. Historical failures before App **Contents: Write** upgrade are documented, not blocking. Permission fix: [RR-V4 findings](../review-pipeline/revy-review-dogfood/REVY_REVIEW_DOGFOOD_RR_V4_FINDINGS.md) · [GITHUB_APP_SETUP.md](../utils/GITHUB_APP_SETUP.md) § Contents Write.
