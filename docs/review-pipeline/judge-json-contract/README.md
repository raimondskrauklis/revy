# Judge JSON contract — program index

**Status:** general plan ready — **execution plans in progress** on `feat/judge-json-contract`.

**Problem:** Anthropic judge returns HTTP 200 but Revy often fails to parse/persist `outcome` → no `github_finding_judge_outcomes` row → RG-6 withholds escalation inline publish.

**Not in scope:** Moonshot review JSON (healthy on staging); finding-resolution closure schema (`0028`).

| Doc | Purpose |
|-----|---------|
| [JUDGE_JSON_CONTRACT_FINDINGS.md](./JUDGE_JSON_CONTRACT_FINDINGS.md) | Baseline — where we are, goals, locked decisions, API smoke |
| [JUDGE_JSON_CONTRACT_GENERAL_PLAN.md](./JUDGE_JSON_CONTRACT_GENERAL_PLAN.md) | P0–P5 phases (general — no execution steps) |
| `waves/JUDGE_JSON_CONTRACT_EXECUTION.md` | LOOP index — added in execution-plan commit |

**Incident / staging evidence:** [FINDING_RESOLUTION_TECHNICAL_FINDINGS.md](../finding-resolution/FINDING_RESOLUTION_TECHNICAL_FINDINGS.md) (PR #57 `c0522ec` dogfood).

**Related programs**

| Program | Link |
|---------|------|
| Judge input quality (shipped) | [judge/README.md](../judge/README.md) |
| Finding resolution (in flight) | [finding-resolution/README.md](../finding-resolution/README.md) |
| RC-D13 / RC-D17 (Moonshot modes) | [REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md](../REVIEW_PIPELINE_CODE_REVIEW_LEARNINGS.md) |

**Related code**

| Area | Path |
|------|------|
| Judge LLM + parse | `backend/app/integrations/anthropic_review.py` |
| Judge loop + manifest | `backend/app/services/github_finding_judge.py` |
| Prompt + evidence context | `backend/app/services/github_review.py` |
| RG-6 publish gate | `backend/app/services/github_publish.py` |
| Gateway smoke script | `backend/scripts/test_anthropic_judge_gateway.py` |

**Staging DB** — `PRODUCTION_DATABASE_URL` → `revy-staging` ([DATABASE_CONNECTION_GUIDE.md](../../utils/DATABASE_CONNECTION_GUIDE.md)).

**LLM path (keep simple):** Revy judge uses **RTU Anthropic Messages API** — `ANTHROPIC_BASE_URL` + `ANTHROPIC_AUTH_TOKEN` → `{base}/v1/messages`. No extra proxy layer required for the app. [llm-rdi-services-runbook.md](../../utils/llm-rdi-services-runbook.md) is a separate LiteLLM stack for Cursor; optional for Revy workers.

**Next step:** `create-execution-plan` → `waves/JUDGE_JSON_CONTRACT_EXECUTION.md` + P0–P5 execution files.
