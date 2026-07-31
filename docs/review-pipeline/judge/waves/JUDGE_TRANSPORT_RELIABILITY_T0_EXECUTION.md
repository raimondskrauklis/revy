# docs/review-pipeline/judge/waves/JUDGE_TRANSPORT_RELIABILITY_T0_EXECUTION.md

# T0 — Incident baseline & prerequisites (execution)

Phase **T0** of [JUDGE_TRANSPORT_RELIABILITY_GENERAL_PLAN.md](../JUDGE_TRANSPORT_RELIABILITY_GENERAL_PLAN.md). Baseline: [JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md](../JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md) § Operator incident, JT-Q2. **T0 only.**

**Goal:** Close JT-Q2 from pipeline manifest; document dual-credential staging requirement; capture metrics baseline before code changes.

## Decisions locked for T0

- Incident repro: PR #72 head `77300aba5b7ae6da1315c43ed349b706f95c55d9` (~2026-07-31 06:26 UTC) unless manifest row missing — then document nearest judge-candidate run on PR #72.
- JT-Q2 resolution recorded in findings § Operator incident (append **Root cause confirmed**).
- Staging env gate: `ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN` + `ANTHROPIC_API_KEY` all required on worker droplet.
- Metrics `--since` anchor: post–#71 D0 deploy `2026-07-30T08:28:45Z` ([finding-resolution D0](../../finding-resolution/waves/FINDING_RESOLUTION_POST_WAVE_C_D0_EXECUTION.md), staging memo Wave D).
- No backend code changes in T0.

## Out of scope for T0

- Transport logging code → **T1**
- Profile fallback hardening → **T2**
- RTU smoke while gateway down → **T3** (partial gate on direct only)
- SSOT / Greptile / Bugbot → **T1.0** (first code phase)

---

## T0.1 — Pipeline manifest query (JT-Q2)

**What:** Run manifest SQL from findings § Experiment / verification for PR #72 `77300ab`. Extract `candidates[].parse_error`, `raw_response_text` (truncate in doc), `retry_count`, prompt length.

**Files:** `docs/review-pipeline/judge/JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md` (append **Root cause confirmed**)

**Deliverable:**

```bash
cd backend && DATABASE_SSL_INSECURE=1 pipenv run python -c "
import asyncio, json
from sqlalchemy import text
from app.core.database import get_db_context

SQL = '''
SELECT rev.head_sha, rr.id AS review_run_id, rr.judge_status,
       rr.judge_escalation_candidate_count,
       a.content_json -> 'candidates' AS candidates
FROM github_review_runs rr
JOIN github_pull_request_revisions rev ON rev.id = rr.revision_id
JOIN github_pull_requests pr ON pr.id = rev.pull_request_id
JOIN github_pipeline_runs p ON p.review_run_id = rr.id
JOIN github_pipeline_steps s ON s.pipeline_run_id = p.id AND s.step_type = 'judge'
JOIN github_pipeline_artifacts a ON a.step_id = s.id AND a.kind = 'manifest'
WHERE pr.number = 72 AND rev.head_sha LIKE '77300aba%' AND rr.status = 'completed'
ORDER BY rr.created_at DESC LIMIT 1
'''

async def main():
    async with get_db_context() as session:
        row = (await session.execute(text(SQL))).first()
        print(json.dumps(dict(row._mapping) if row else {}, indent=2, default=str))

asyncio.run(main())
"
```

JT-Q2 decisions row → **locked** with one-sentence root cause in findings.

---

## T0.2 — Metrics baseline snapshot

**What:** Run `judge_json_contract_staging_metrics` with D0 deploy boundary; save JSON in validation memo stub.

**Files:** `docs/review-pipeline/judge/JUDGE_TRANSPORT_RELIABILITY_STAGING_VALIDATION.md` (create stub)

**Deliverable:**

```bash
cd backend && DATABASE_SSL_INSECURE=1 pipenv run python -m scripts.judge_json_contract_staging_metrics --since 2026-07-30T08:28:45Z --json > /tmp/judge_transport_baseline.json
```

Record `all_failed`, `skipped_unavailable`, `candidate_runs` in memo § Baseline. Anchor: post–#71 deploy (Wave D).

---

## T0.3 — Dual-credential env gate

**What:** Document staging worker requirement in deploy env example and validation memo § Pre-flight. List three vars and `judge_llm_enabled()` expectation.

**Files:** `deploy/env-examples/backend.env.production.example`, `backend/.env.example`, `JUDGE_TRANSPORT_RELIABILITY_STAGING_VALIDATION.md`

**Deliverable:** Env examples comment block “Judge transport — gateway + direct fallback (JT-Q6)”; memo pre-flight table with PASS/FAIL placeholders.

---

## T0.4 — Incident narrative sync

**What:** Append **Root cause confirmed** paragraph to findings § Operator incident; link validation memo stub; confirm JT-Q2 **locked** in decisions registry.

**Files:** `JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md`

**Deliverable:** Findings § Operator incident includes confirmed root cause; decisions registry JT-Q2 status **locked**.

---

**Phase gate** (doc-only — no pytest):

```bash
test -f docs/review-pipeline/judge/JUDGE_TRANSPORT_RELIABILITY_STAGING_VALIDATION.md
rg '\| \*\*JT-Q2\*\* \|.*\| \*\*locked\*\*' docs/review-pipeline/judge/JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md
rg 'Root cause confirmed' docs/review-pipeline/judge/JUDGE_TRANSPORT_RELIABILITY_FINDINGS.md
```

**Human gate:** Staging DB access for T0.1–T0.2 (operator).

**Next:** [JUDGE_TRANSPORT_RELIABILITY_T1_EXECUTION.md](./JUDGE_TRANSPORT_RELIABILITY_T1_EXECUTION.md)
