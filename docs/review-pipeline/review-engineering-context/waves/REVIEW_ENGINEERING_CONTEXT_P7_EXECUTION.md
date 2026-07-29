# Review engineering context P7 — Operator visibility (execution)

Phase **P7** of [REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md](../REVIEW_ENGINEERING_CONTEXT_GENERAL_PLAN.md). Baseline: [REVIEW_ENGINEERING_CONTEXT_FINDINGS.md](../REVIEW_ENGINEERING_CONTEXT_FINDINGS.md) § Wave 2, RCX-14, RCX-15, RCX-G11, RCX-G12. **P7 only.**

**Goal:** Operator validates RCX inject and caps without SQL — API exposes `context_stats`; metrics script prints pass/fail gate block.

**Ship with P6:** Same PR branch (RCX-D15) — both touch `backend/**`.

## Decisions locked for P7

- **API shape:** `context_stats: dict[str, Any] | None` on `GitHubReviewRunResponse` — raw JSONB from ORM (keys per `ContextStats` in `engineering_context/stats.py`).
- **No new endpoint** — `installation_review.py` uses `GitHubReviewRunResponse.model_validate(run)` only — new field flows automatically.
- **Null when unset** — pre-RCX runs and in-progress runs return `null`.
- **`--rcx-gate` behavior:** Gate block prints **only when** `--rcx-gate` is passed (not by default). `--json` includes `rcx_gate` object **only when** `--rcx-gate` is also passed.
- **Inject gate source (locked):** Primary = `context_stats` SQL aggregate (`runs_with_context_stats`, `engineering_context_injected_runs` from `github_review_runs.context_stats`). Cross-check = retrieve manifest `engineering_context_injected_runs` — gate **FAIL** if context_stats says injected but retrieve manifest count is 0 on same window.
- **Gate targets (post-deploy `--since` window):**
  - `runs_with_context_stats` ≥ 1 (when scoped completed runs > 0)
  - `engineering_context_injected_runs` (context_stats) ≥ 1 (when scoped runs > 0)
  - `engineering_context_bytes_p50` > 0 when inject runs > 0
  - `runs_with_omitted_md` = 0
  - `diff_truncated_pct` < 5.0 when completed runs ≥ 3; **INCONCLUSIVE** (not FAIL) when runs 1–2 (single dogfood PR — RCX-D15)
- **Without `--since`:** Print warning — gate uses full history (baseline mode); operator should not sign off on that output.
- **Script rename** deferred (parking lot).

## Out of scope for P7

- Frontend reviewer UI for `context_stats`
- Pipeline trace artifact browser changes
- Staging memo fill → **P8**

---

## P7.1 — Schema + response field

**What:** Add `context_stats: dict[str, Any] | None = None` to `GitHubReviewRunResponse`.

**Files:** `backend/app/schemas/github_review.py`

**Deliverable:**

```bash
cd backend && pipenv run ruff check app/schemas/github_review.py
cd backend && pipenv run python -c "from app.schemas.github_review import GitHubReviewRunResponse; assert 'context_stats' in GitHubReviewRunResponse.model_fields"
```

---

## P7.2 — API unit test

**What:** Test `GitHubReviewRunResponse.model_validate(run)` with full `ContextStats`-shaped dict:

```python
context_stats = {
    "active_program": "review-engineering-context",
    "diff_max_bytes": 524288,
    "unified_diff_bytes": 120000,
    "diff_truncated": False,
    "omitted_files_count": 0,
    "omitted_md_count": 0,
    "engineering_context_injected": True,
    "engineering_context_bytes": 4096,
    "engineering_context_deduped_paths": [],
    "lock_ids_extracted": ["RCX-D8"],
    "engineering_context_errors": [],
    "prompt_chars": 150000,
}
```

**Files:** `backend/tests/unit/test_github_review.py`

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_github_review.py -k "context_stats or ReviewRunResponse" -q
```

---

## P7.3 — Verify API routes (no manual dict drop)

**What:** Confirm `app/api/v1/workspaces/installation_review.py` only uses `model_validate(run)` — no gap to fix unless manual dict found.

**Deliverable:**

```bash
cd backend && rg "GitHubReviewRunResponse" app/api/ && \
  ! rg "GitHubReviewRunResponse\\(" app/api/ --glob "*.py"
```

(Second line must produce no matches — construction only via `model_validate`.)

---

## P7.4 — Metrics script RCX gate block

**What:** Add `--rcx-gate` flag; implement `_evaluate_rcx_gate(metrics) -> dict` using rules in **Decisions locked** above. Human summary when flag set:

```text
RCX gate (--since window):
  [PASS|FAIL|INCONCLUSIVE] context_stats rows >= 1
  [PASS|FAIL] engineering_context_injected (context_stats) >= 1
  [PASS|FAIL] engineering_context_bytes p50 > 0
  [PASS|FAIL] runs_with_omitted_md = 0
  [PASS|FAIL|INCONCLUSIVE] diff_truncated_pct < 5%
  [PASS|FAIL] retrieve manifest inject cross-check
```

`passed` = all PASS (INCONCLUSIVE checks excluded from failure).

**Files:** `backend/scripts/judge_json_contract_staging_metrics.py`

**Deliverable:**

```bash
cd backend && pipenv run python -m scripts.judge_json_contract_staging_metrics --help | grep rcx-gate
```

---

## P7.5 — Script unit test

**What:** Test `_evaluate_rcx_gate` — pass, fail omitted md, inconclusive truncated (1 run), cross-check mismatch.

**Files:** `backend/tests/unit/test_judge_json_contract_staging_metrics.py` (create)

**Deliverable:**

```bash
cd backend && pipenv run pytest tests/unit/test_judge_json_contract_staging_metrics.py -q
```

---

## P7.6 — Metrics runbook (create missing doc)

**What:** `docs/utils/BACKEND_SCRIPTS_RUNBOOK.md` is **referenced by judge-json-contract P0** but **does not exist yet** — create minimal runbook with § Staging metrics:

```bash
cd backend
DATABASE_SSL_INSECURE=1 pipenv run sh -c 'python -m scripts.judge_json_contract_staging_metrics'
DATABASE_SSL_INSECURE=1 pipenv run sh -c 'python -m scripts.judge_json_contract_staging_metrics --since <iso> --json'
DATABASE_SSL_INSECURE=1 pipenv run sh -c 'python -m scripts.judge_json_contract_staging_metrics --since <iso> --rcx-gate'
```

Also add one-line pointer in [JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md](../../judge-json-contract/JUDGE_JSON_CONTRACT_STAGING_VALIDATION.md) metrics header if runbook link is broken today.

**Files:** `docs/utils/BACKEND_SCRIPTS_RUNBOOK.md` (new), optional link fix in judge validation memo

**Deliverable:**

```bash
test -f docs/utils/BACKEND_SCRIPTS_RUNBOOK.md && grep -q rcx-gate docs/utils/BACKEND_SCRIPTS_RUNBOOK.md
```

---

**Phase gate** (from `backend/`):

```bash
pipenv run ruff check app/schemas/github_review.py scripts/judge_json_contract_staging_metrics.py
pipenv run pytest tests/unit/test_github_review.py tests/unit/test_judge_json_contract_staging_metrics.py -q
```

**Next:** [REVIEW_ENGINEERING_CONTEXT_P8_EXECUTION.md](./REVIEW_ENGINEERING_CONTEXT_P8_EXECUTION.md)
