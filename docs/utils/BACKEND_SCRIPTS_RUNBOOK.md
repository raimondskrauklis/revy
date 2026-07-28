# Backend operator scripts — agent runbook

Short reference for running one-off scripts from `backend/`. For agents and operators validating LLM paths before deploy.

**Related:** [JUDGE_JSON_CONTRACT_FINDINGS.md](../review-pipeline/judge-json-contract/JUDGE_JSON_CONTRACT_FINDINGS.md) § P0 smoke · [DEV_BOOTSTRAP.md](../starter-pack/DEV_BOOTSTRAP.md) § bootstrap seed

---

## Prerequisites

| Item | Rule |
|------|------|
| **Working directory** | Always `cd backend` first |
| **Dependencies** | `pip install -r requirements/dev.txt` inside the project venv (Revy uses **requirements**, not Pipfile packages) |
| **Env** | Copy `backend/.env.example` → `backend/.env`; judge smoke needs RTU or direct Anthropic vars (see below) |
| **Module imports** | Scripts live under `backend/scripts/` — run as **`python -m scripts.<module>`**, not `python scripts/foo.py` (avoids `ModuleNotFoundError: app`) |

---

## Pipenv invocation

Use **`pipenv run`** from `backend/` so `.env` loads and the venv is active.

**Important:** Pipenv treats bare `-m` as its own flag. Wrap the full Python command in `sh -c '…'`:

```bash
cd backend
pipenv run sh -c 'python -m scripts.<module> [args]'
```

Examples:

```bash
# Bootstrap super admin (one-time)
pipenv run sh -c 'python -m scripts.seed_bootstrap_super_admin'

# Judge gateway smoke — help
pipenv run sh -c 'python -m scripts.test_anthropic_judge_gateway --help'
```

Do **not** rely on `pipenv run python -m …` without `sh -c` — it may print pipenv usage instead of running the script.

---

## Judge smoke (`scripts.test_anthropic_judge_gateway`)

Validates RTU Anthropic Messages API (`ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN`) and optional direct fallback (`ANTHROPIC_API_KEY`). Used in [judge-json-contract P0](../review-pipeline/judge-json-contract/waves/JUDGE_JSON_CONTRACT_P0_EXECUTION.md).

### Env (minimal)

```text
ANTHROPIC_BASE_URL=https://llm.ai.rtu.lv
ANTHROPIC_AUTH_TOKEN=…
REVY_ANTHROPIC_GATEWAY_MODEL=azure_ai/claude-sonnet-5
```

Optional direct path: `ANTHROPIC_API_KEY=…`

### P0 matrix (run from `backend/`)

```bash
# Plain prompt JSON (gateway + fallback chain)
pipenv run sh -c 'python -m scripts.test_anthropic_judge_gateway'

# Structured output (output_config json_schema)
pipenv run sh -c 'python -m scripts.test_anthropic_judge_gateway --structured --print-raw'

# Per-profile side-by-side (gateway vs direct when both configured)
pipenv run sh -c 'python -m scripts.test_anthropic_judge_gateway --compare-direct'

# Prompt size sweep
pipenv run sh -c 'python -m scripts.test_anthropic_judge_gateway --chars 1000'
pipenv run sh -c 'python -m scripts.test_anthropic_judge_gateway --chars 10000'

# Replay staging manifest prompt export
pipenv run sh -c 'python -m scripts.test_anthropic_judge_gateway --prompt-file /path/to/prompt.txt'
```

### Exit codes

| Code | Meaning |
|------|---------|
| `0` | Parsed `outcome` in `upheld` \| `dismissed` \| `modified` |
| `1` | Not configured, HTTP error (e.g. **401** bad token), or JSON/parse failure |

Record results in findings § **P0 smoke results** before locking P3 structured output.

### Common failures

| Symptom | Fix |
|---------|-----|
| `ModuleNotFoundError: app` | Wrong cwd or used `python scripts/…py` — use `-m` from `backend/` |
| `401 Unauthorized` | Refresh `ANTHROPIC_AUTH_TOKEN` in `backend/.env` |
| `Judge LLM not configured` | Set gateway URL + token or `ANTHROPIC_API_KEY` |
| Pipenv prints `usage: pipenv run` | Missing `sh -c '…'` wrapper around `python -m` |

---

## Judge staging metrics (`scripts.judge_json_contract_staging_metrics`)

P5 validation aggregates on `revy-staging` — outcome persistence, prompt p50, `parse_error` / `retry_count` on manifests.

### Env

```text
PRODUCTION_DATABASE_URL=postgresql+asyncpg://revy-user-staging:…/revy-staging?ssl=require
DATABASE_SSL_INSECURE=1
```

### Run

```bash
cd backend
DATABASE_SSL_INSECURE=1 pipenv run sh -c 'python -m scripts.judge_json_contract_staging_metrics'
DATABASE_SSL_INSECURE=1 pipenv run sh -c 'python -m scripts.judge_json_contract_staging_metrics --since 2026-07-29T00:00:00Z --json'
```

Record output in [JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md](../review-pipeline/judge-json-contract/JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md).

---

## Adding a new script

1. Add `backend/scripts/<name>.py` with line-1 path comment.
2. Ensure `backend/scripts/__init__.py` exists (package marker).
3. Document run line: `pipenv run sh -c 'python -m scripts.<name>'`.
4. No production import from `scripts/` — operator/dev only.
